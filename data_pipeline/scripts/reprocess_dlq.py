"""
scripts/reprocess_dlq.py — Manual DLQ reprocessing tool.

Reads failed ingestion events from the SQS Dead Letter Queue, shows what
failed, and re-invokes the Lambda function with the original S3 event.
Deletes a message from SQS only after Lambda confirms success.

Usage:
    python scripts/reprocess_dlq.py [--stage dev|prod] [--dry-run]

Requirements:
    AWS credentials with sqs:ReceiveMessage, sqs:DeleteMessage,
    lambda:InvokeFunction on the ingestion function.
    Profile: zygotrix (matches serverless.yml)
"""

import argparse
import json
import sys

import boto3

REGION = "ap-south-1"
PROFILE = "zygotrix"
SERVICE = "trademate-ingestion-pipeline"


def get_queue_url(sqs, stage: str) -> str:
    queue_name = f"{SERVICE}-{stage}-dlq"
    response = sqs.get_queue_url(QueueName=queue_name)
    return response["QueueUrl"]


def get_function_name(stage: str) -> str:
    return f"{SERVICE}-{stage}-ingestion"


def parse_dlq_message(body: str) -> dict:
    """
    Extract the original S3 event from the Lambda Destinations failure envelope.

    AWS wraps failed async invocations in an envelope with shape:
    {
      "requestContext": { "condition": "RetriesExhausted", ... },
      "requestPayload": { <original S3 event> },
      "responseContext": { "functionError": "Unhandled", ... }
    }
    """
    envelope = json.loads(body)
    original_event = envelope.get("requestPayload")
    if not original_event:
        raise ValueError("No requestPayload in DLQ message — unexpected format")
    return original_event, envelope


def reprocess(stage: str, dry_run: bool) -> None:
    session = boto3.Session(profile_name=PROFILE, region_name=REGION)
    sqs = session.client("sqs")
    lambda_client = session.client("lambda")

    queue_url = get_queue_url(sqs, stage)
    function_name = get_function_name(stage)

    print(f"\nDLQ:      {queue_url}")
    print(f"Function: {function_name}")
    print(f"Dry run:  {dry_run}\n")

    processed = skipped = failed = 0

    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=5,         # long poll — avoids empty responses
            VisibilityTimeout=120,     # hold message while we re-invoke Lambda
            AttributeNames=["ApproximateReceiveCount"],
            MessageAttributeNames=["All"],
        )

        messages = response.get("Messages", [])
        if not messages:
            print("No more messages in DLQ.")
            break

        for msg in messages:
            receipt = msg["ReceiptHandle"]
            receive_count = msg.get("Attributes", {}).get("ApproximateReceiveCount", "?")

            try:
                original_event, envelope = parse_dlq_message(msg["Body"])
            except (ValueError, KeyError, json.JSONDecodeError) as exc:
                print(f"  [SKIP] Could not parse message — {exc}")
                skipped += 1
                continue

            # Show what failed
            try:
                s3_key = original_event["Records"][0]["s3"]["object"]["key"]
            except (KeyError, IndexError):
                s3_key = "<unknown>"

            condition = envelope.get("requestContext", {}).get("condition", "?")
            error = envelope.get("responseContext", {}).get("functionError", "?")

            print(f"  S3 key:       {s3_key}")
            print(f"  Condition:    {condition}")
            print(f"  Error type:   {error}")
            print(f"  Receive count: {receive_count}")

            if dry_run:
                print("  [DRY RUN] Would re-invoke Lambda — skipping.\n")
                skipped += 1
                continue

            confirm = input("  Re-invoke Lambda for this event? [y/N] ").strip().lower()
            if confirm != "y":
                print("  Skipped.\n")
                skipped += 1
                continue

            # Re-invoke Lambda synchronously so errors surface immediately
            print("  Invoking Lambda...", end=" ", flush=True)
            invoke_response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType="RequestResponse",  # synchronous
                Payload=json.dumps(original_event).encode(),
            )

            status_code = invoke_response["StatusCode"]
            function_error = invoke_response.get("FunctionError")
            response_payload = json.loads(invoke_response["Payload"].read())

            if function_error or status_code != 200:
                print(f"FAILED (status={status_code}, error={function_error})")
                print(f"  Response: {response_payload}\n")
                failed += 1
                # Do NOT delete — leave in DLQ for another attempt
            else:
                print(f"OK (status={status_code})")
                # Delete from DLQ only after confirmed success
                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt)
                print("  Deleted from DLQ.\n")
                processed += 1

    print(f"\nDone — processed: {processed}  skipped: {skipped}  failed: {failed}")
    if failed:
        print("Failed messages remain in the DLQ and will become visible again after the visibility timeout.")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reprocess failed ingestion events from the DLQ")
    parser.add_argument("--stage", default="dev", choices=["dev", "prod"], help="Deployment stage")
    parser.add_argument("--dry-run", action="store_true", help="List messages without re-invoking Lambda")
    args = parser.parse_args()

    reprocess(stage=args.stage, dry_run=args.dry_run)
