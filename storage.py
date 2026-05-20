import boto3
import os
from botocore.config import Config

def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=os.getenv('R2_ENDPOINT'),
        aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
        config=Config(signature_version='s3v4'),
        region_name='auto'
    )

def upload_file(file_bytes: bytes, filename: str, content_type: str) -> str:
    client = get_s3_client()
    bucket = os.getenv('R2_BUCKET')
    client.put_object(
        Bucket=bucket,
        Key=filename,
        Body=file_bytes,
        ContentType=content_type
    )
    return filename