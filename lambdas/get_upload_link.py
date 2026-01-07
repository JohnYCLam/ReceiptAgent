import json
import boto3
import uuid
import os
from botocore.client import Config

# Initialize S3 with specific Region and SigV4 to prevent "400 Bad Request"
s3 = boto3.client('s3', 
                  region_name=os.environ.get('AWS_REGION'),
                  config=Config(signature_version='s3v4'))

def lambda_handler(event, context):
    # 1. DEFINE HEADERS (The "Keys" to the door)
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
    }

    # 2. HANDLE PRE-FLIGHT (OPTIONS request)
    if event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps("OK")}

    try:
        bucket_name = os.environ['BUCKET_NAME']
        file_name = f"receipts/{uuid.uuid4()}.jpg"
        
        # 3. Generate URL (enforcing image/jpeg)
        url = s3.generate_presigned_url('put_object',
                                        Params={'Bucket': bucket_name,
                                                'Key': file_name,
                                                'ContentType': 'image/jpeg'},
                                        ExpiresIn=300)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'upload_url': url, 'filename': file_name})
        }

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps(f"Error: {str(e)}")
        }