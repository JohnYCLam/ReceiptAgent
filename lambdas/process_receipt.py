import json
import boto3
import os
import urllib.parse
import time
from decimal import Decimal

textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        # 1. Get Event Details & Decode Filename
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        raw_key = record['s3']['object']['key']
        key = urllib.parse.unquote_plus(raw_key)
        
        print(f"Processing: {key} from {bucket}")
        
        # 2. Call Textract
        response = textract.analyze_expense(
            Document={'S3Object': {'Bucket': bucket, 'Name': key}}
        )
        
        # 3. Simple Parser (Extract Total & Merchant)
        merchant = "Unknown Store"
        total = "0.00"
        
        for doc in response.get('ExpenseDocuments', []):
            for field in doc.get('SummaryFields', []):
                ftype = field.get('Type', {}).get('Text', '')
                ftext = field.get('ValueDetection', {}).get('Text', '')
                
                if ftype == 'VENDOR_NAME':
                    merchant = ftext
                elif ftype == 'TOTAL':
                    total = ftext.replace('$', '').replace(',', '')

        print(f"Extracted: {merchant} - ${total}")

        # 4. Save to DynamoDB
        table = dynamodb.Table(os.environ['TABLE_NAME'])
        table.put_item(Item={
            'UserId': 'demo_user',
            'Timestamp': str(time.time()),
            'Merchant': merchant,
            'Total': total,
            'Image': key
        })
        
        return {"statusCode": 200, "body": "Success"}
        
    except Exception as e:
        print(f"Error: {e}")
        raise e