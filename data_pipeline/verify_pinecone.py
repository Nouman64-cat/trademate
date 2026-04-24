import os
import sys
from dotenv import load_dotenv
from pinecone import Pinecone
import boto3
import json


def verify_pinecone():
    # Load environment variables from .env
    load_dotenv()

    # If manual AWS credentials are provided in .env (AWS_ACCESS_KEY_ID_MANUAL
    # / AWS_SECRET_ACCESS_KEY_MANUAL), export them to the names boto3 expects
    # so local S3 operations succeed without requiring an AWS profile.
    if not os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_ACCESS_KEY_ID_MANUAL"):
        os.environ["AWS_ACCESS_KEY_ID"] = os.environ.get(
            "AWS_ACCESS_KEY_ID_MANUAL")
    if not os.environ.get("AWS_SECRET_ACCESS_KEY") and os.environ.get("AWS_SECRET_ACCESS_KEY_MANUAL"):
        os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ.get(
            "AWS_SECRET_ACCESS_KEY_MANUAL")
    # Ensure region is set for boto3
    if not os.environ.get("AWS_REGION") and os.environ.get("AWS_REGION"):
        os.environ["AWS_REGION"] = os.environ.get("AWS_REGION")

    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "trademate-documents")

    if not api_key:
        print("❌ Error: PINECONE_API_KEY not found in .env file.")
        print("Please ensure you are running this from the directory containing your .env file.")
        sys.exit(1)

    print(f"Connecting to Pinecone index: {index_name}...")

    try:
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)

        # Fetch index statistics
        stats = index.describe_index_stats()

        print("\n" + "="*40)
        print(f"  PINECONE VERIFICATION SUCCESS")
        print("="*40)
        print(f"  Index Name:    {index_name}")
        print(f"  Total Vectors: {stats['total_vector_count']}")
        print(f"  Dimension:     {stats.get('dimension', 'N/A')}")
        print("="*40)

        if stats['total_vector_count'] > 0:
            print("\n✅ Your research pipeline is successfully storing data!")
        else:
            print(
                "\n⏳ The index is currently empty. Run the research pipeline to populate it.")

    except Exception as e:
        print(f"\n❌ Error connecting to Pinecone: {e}")
        sys.exit(1)

    # Additionally, list the last 3 research JSON files stored in S3 (if configured).
    bucket = os.getenv("AWS_S3_BUCKET_NAME")
    if not bucket:
        print("\nNote: AWS_S3_BUCKET_NAME not set; skipping S3 lookup for recent research files.")
        return

    try:
        s3 = boto3.client("s3")
        resp = s3.list_objects_v2(Bucket=bucket, Prefix="research/")
        contents = resp.get("Contents", [])
        if not contents:
            print(f"\nNo research objects found in s3://{bucket}/research/")
            return

        # sort by LastModified descending and take the last 3
        contents.sort(key=lambda x: x.get("LastModified"), reverse=True)
        last3 = contents[:3]

        print("\n" + "="*40)
        print("  Last 3 research objects in S3")
        print("="*40)
        for obj in last3:
            key = obj["Key"]
            lm = obj.get("LastModified")
            size = obj.get("Size")
            print(f"- {key}  ({lm}, {size} bytes)")
            try:
                data = s3.get_object(Bucket=bucket, Key=key)
                body = data["Body"].read().decode("utf-8")
                # Try to pretty-print JSON, otherwise print a truncated preview
                try:
                    parsed = json.loads(body)
                    pretty = json.dumps(parsed, indent=2)
                    preview = "\n" + pretty[:2000]
                except Exception:
                    preview = "\n" + body[:2000]
                print(preview)
            except Exception as e:
                print(f"  (failed to fetch object data: {e})")

    except Exception as e:
        print(f"\nError while listing S3 research objects: {e}")
        return


if __name__ == "__main__":
    verify_pinecone()
