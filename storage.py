import httpx
import os
import hmac
import hashlib
import datetime

def upload_file(file_bytes: bytes, filename: str, content_type: str) -> str:
    endpoint = os.getenv('R2_ENDPOINT')
    bucket = os.getenv('R2_BUCKET')
    access_key = os.getenv('R2_ACCESS_KEY_ID')
    secret_key = os.getenv('R2_SECRET_ACCESS_KEY')
    
    url = f"{endpoint}/{bucket}/{filename}"
    
    now = datetime.datetime.utcnow()
    date_stamp = now.strftime('%Y%m%d')
    amz_date = now.strftime('%Y%m%dT%H%M%SZ')
    
    with httpx.Client() as client:
        response = client.put(
            url,
            content=file_bytes,
            headers={
                'Content-Type': content_type,
                'x-amz-date': amz_date,
            },
            auth=None
        )
    return filename