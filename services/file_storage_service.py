# safeagree_backend/services/file_storage_service.py
# Manages interactions with file storage (e.g., AWS S3 or local file system).
import boto3
import json
import os
from botocore.exceptions import ClientError

# AWS S3 configuration from environment variables
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "safeagree")
AWS_REGION = os.getenv("AWS_REGION", "eu-north-1") # Example region

class FilebaseManager:
    """
    Manages file storage and retrieval from AWS S3.
    """
    def __init__(self,AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME, AWS_REGION):
        if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME, AWS_REGION]):
            print("WARNING: AWS S3 credentials or bucket name not fully configured. S3 operations will fail.")
            self.s3_client = None
        else:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION
            )

    def upload_json_to_s3(self, file_name, json_data):
        """
        Uploads a JSON object to an S3 bucket.
        :param file_name: S3 object key (e.g., 'policy_summary_123.json')
        :param json_data: Python dictionary to be stored as JSON
        :return: True if upload successful, False otherwise
        """
        if not self.s3_client:
            print("S3 client not initialized. Cannot upload.")
            return False
        try:
            json_string = json.dumps(json_data)
            self.s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=file_name, Body=json_string, ContentType='application/json')
            print(f"Successfully uploaded {file_name} to S3 bucket {S3_BUCKET_NAME}")
            return True
        except ClientError as e:
            print(f"Error uploading {file_name} to S3: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during S3 upload: {e}")
            return False

    def get_json_from_s3(self, file_name):
        """
        Retrieves a JSON object from an S3 bucket.
        :param file_name: S3 object key
        :return: Python dictionary if successful, None otherwise
        """
        if not self.s3_client:
            print("S3 client not initialized. Cannot retrieve.")
            return None
        try:
            response = self.s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=file_name)
            json_data = json.loads(response['Body'].read().decode('utf-8'))
            print(f"Successfully retrieved {file_name} from S3 bucket {S3_BUCKET_NAME}")
            return json_data
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                print(f"File {file_name} not found in S3.")
            else:
                print(f"Error retrieving {file_name} from S3: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during S3 retrieval: {e}")
            return None
        
    def delete_file_from_s3(self, file_name):
        """Deletes a file from S3."""
        if not self.s3:
            print("S3 client not initialized. Cannot delete.")
            return False
        try:
            self.s3.delete_object(Bucket=self.s3_bucket_name, Key=file_name)
            print(f"Successfully deleted {file_name} from S3.")
            return True
        except ClientError as e:
            print(f"Error deleting {file_name} from S3: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during S3 deletion: {e}")
            return False