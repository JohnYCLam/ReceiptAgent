import json
import boto3
import os
from boto3.dynamodb.conditions import Key

bedrock = boto3.client(service_name='bedrock-runtime')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        question = body.get('question', 'How much did I spend?')
        
        # 1. Fetch recent expenses from DB
        table = dynamodb.Table(os.environ['TABLE_NAME'])
        response = table.query(
            KeyConditionExpression=Key('UserId').eq('demo_user'),
            ScanIndexForward=False, # Newest first
            Limit=5
        )
        
        # Format data for AI
        expenses = "\n".join([f"- {i['Merchant']}: ${i['Total']}" for i in response['Items']])
        prompt = f"Here is my recent spending:\n{expenses}\n\nUser Question: {question}\nAnswer:"
        
        # 2. Call Bedrock (Claude 3)
        # Note: Ensure you have requested access to 'anthropic.claude-3-haiku-...' in Model Access
        model_id = "anthropic.claude-3-haiku-20240307-v1:0" 
        
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 300,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ]
        }
        
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(payload)
        )
        
        result = json.loads(response['body'].read())
        answer = result['content'][0]['text']
        
        return {
            'statusCode': 200,
            'body': json.dumps({'answer': answer})
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {'statusCode': 500, 'body': json.dumps({'answer': "Error connecting to AI. Check logs."})}