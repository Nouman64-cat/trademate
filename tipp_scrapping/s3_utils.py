import os
import boto3
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("s3-utils")

# Load credentials from .env
BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID_MANUAL")
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY_MANUAL")
REGION = os.getenv("AWS_REGION", "us-east-1")

def get_s3_client():
    if not ACCESS_KEY or not SECRET_KEY:
        logger.warning("AWS credentials not found in environment. S3 operations will fail.")
        return None
    
    return boto3.client(
        's3',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name=REGION
    )

def upload_to_s3(local_file_path, s3_key=None):
    """Upload a local file to S3."""
    s3 = get_s3_client()
    if not s3:
        return False
    
    if s3_key is None:
        s3_key = os.path.basename(local_file_path)
    
    try:
        logger.info(f"Uploading {local_file_path} to s3://{BUCKET_NAME}/{s3_key}...")
        s3.upload_file(local_file_path, BUCKET_NAME, s3_key)
        logger.info("Upload successful.")
        return True
    except Exception as e:
        logger.error(f"Failed to upload to S3: {e}")
        return False

def download_from_s3(s3_key, local_file_path):
    """Download a file from S3 to local storage."""
    s3 = get_s3_client()
    if not s3:
        return False
    
    try:
        logger.info(f"Downloading s3://{BUCKET_NAME}/{s3_key} to {local_file_path}...")
        s3.download_file(BUCKET_NAME, s3_key, local_file_path)
        logger.info("Download successful.")
        return True
    except Exception as e:
        # If file doesn't exist, it's often okay (e.g. first run)
        logger.debug(f"Could not download {s3_key} from S3: {e}")
        return False

def sync_data_to_s3(data_dir="data"):
    """Sync all CSV and TXT files in data_dir to S3."""
    if not os.path.exists(data_dir):
        return
    
    files = [f for f in os.listdir(data_dir) if f.endswith(('.csv', '.txt', '.log'))]
    for filename in files:
        local_path = os.path.join(data_dir, filename)
        upload_to_s3(local_path, f"tipp-data/{filename}")

def sync_data_from_s3(data_dir="data"):
    """Download existing data files from S3 to resume."""
    s3 = get_s3_client()
    if not s3:
        return
    
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix="tipp-data/")
        if 'Contents' in response:
            for obj in response['Contents']:
                s3_key = obj['Key']
                filename = os.path.basename(s3_key)
                if filename:
                    local_path = os.path.join(data_dir, filename)
                    download_from_s3(s3_key, local_path)
    except Exception as e:
        logger.error(f"Failed to sync from S3: {e}")
