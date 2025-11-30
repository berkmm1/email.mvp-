# MinIO/S3 upload ve yardımcı fonksiyonlar
import boto3
import os
import base64

def upload_to_minio(file_bytes: bytes, filename: str):
    s3 = boto3.client(
        "s3",
        endpoint_url=os.getenv("MINIO_ENDPOINT", "http://localhost:9000"),
        aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        region_name="us-east-1"
    )
    bucket = os.getenv("MINIO_BUCKET", "attachments")
    try:
        s3.create_bucket(Bucket=bucket)
    except Exception:
        pass
    s3.put_object(Bucket=bucket, Key=filename, Body=file_bytes)
    return f"{bucket}/{filename}"
