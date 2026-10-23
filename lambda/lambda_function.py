import json
import boto3
import os
import base64
from datetime import datetime, UTC
import requests
import dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
# from dotenv import find_dotenv, load_dotenv


# load_dotenv(find_dotenv(usecwd=True), override=True)
s3_client = boto3.client('s3')


def lambda_handler(event, context):
    creds = Credentials(
        token=None,
        refresh_token=os.environ['GMAIL_REFRESH_TOKEN'],
        client_id=os.environ['GMAIL_CLIENT'],
        client_secret=os.environ['GMAIL_SECRET'],
        token_uri="https://oauth2.googleapis.com/token",
    )
    service = build('gmail', 'v1', credentials=creds)
    service_messages = service.users().messages()

    email_result = []
    results = service_messages.list(userId='me', includeSpamTrash=True, maxResults=5).execute()
    for message in results.get('messages'):
        sender = None
        subject = None
        message_id = message.get('id')

        message_result = service_messages.get(userId='me', id=message_id).execute()

        internal_date = message_result.get('internalDate')
        date = datetime.fromtimestamp(int(internal_date) / 1000.0)
        label = message_result.get('labelIds')
        for header in message_result.get('payload').get('headers'):
            if header["name"].lower() == "from":
                sender = header["value"]
            elif header["name"].lower() == "subject":
                subject = header["value"]
        email_result.append({
            "subject": subject,
            "date": date,
            "status":label,
            "from": sender
        })

    runtime = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    bucket_name = os.environ["BUCKET_NAME"]
    file_name = f"gmail_export_{runtime}.json"

    try:
        # Convert dictionary to a deployment-ready JSON string
        json_string = json.dumps(email_result)
        
        # Upload data directly from memory to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=json_string,
            ContentType='application/json'
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps('File uploaded successfully!')
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        raise e