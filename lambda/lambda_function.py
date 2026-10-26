import json
import boto3
import time
import os
from datetime import datetime, UTC
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import urllib.error
import urllib.parse
import urllib.request
# import dotenv
# from dotenv import find_dotenv, load_dotenv


# load_dotenv(find_dotenv(usecwd=True), override=True)
s3_client = boto3.client('s3')
secretsmanager_client = boto3.client('secretsmanager', region_name='ap-southeast-2')

# Simple cache implementation
_cache = {}
CACHE_TTL = 300  # 5 minutes

def get_secret(secret_id):
    cached = _cache.get(secret_id)
    if cached and time.time() - cached['timestamp'] < CACHE_TTL:
        return cached['value']

    response = secretsmanager_client.get_secret_value(SecretId=secret_id)
    secret = json.loads(response['SecretString'])

    _cache[secret_id] = {'value': secret, 'timestamp': time.time()}
    return secret


def upload_to_volume(filename, secretmanager_creds, data: bytes):
    path = urllib.parse.quote(f"/Volumes/email_filter/00_landing/lambda/raw/{filename}")
    req = urllib.request.Request(
        f"{secretmanager_creds['DATABRICKS_HOST']}/api/2.0/fs/files{path}?overwrite=true",
        data=data,
        method="PUT",
        headers={
            "Authorization": f"Bearer {secretmanager_creds['DATABRICKS_TOKEN']}",
            "Content-Type": "application/octet-stream",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        print(f"Databricks upload failed ({e.code}): {e.read().decode('utf-8', errors='replace')}")
        raise


def lambda_handler(event, context):
    secretmanager_creds = get_secret('prod/Lambda')
    creds = Credentials(
        token=None,
        refresh_token=secretmanager_creds['GMAIL_REFRESH_TOKEN'],
        client_id=secretmanager_creds['GMAIL_CLIENT'],
        client_secret=secretmanager_creds['GMAIL_SECRET'],
        token_uri="https://oauth2.googleapis.com/token",
    )
    service = build('gmail', 'v1', credentials=creds)
    service_messages = service.users().messages()

    email_result = []
    results = service_messages.list(userId='me', includeSpamTrash=True, maxResults=50).execute()
    for message in results.get('messages', []):
        sender = None
        subject = None
        message_id = message.get('id')

        message_result = service_messages.get(userId='me', id=message_id).execute()

        internal_date = message_result.get('internalDate')
        date = str(datetime.fromtimestamp(int(internal_date) / 1000.0))
        label = message_result.get('labelIds')
        for header in message_result.get('payload').get('headers'):
            if header["name"].lower() == "from":
                sender = header["value"]
            elif header["name"].lower() == "subject":
                subject = header["value"]
        email_result.append({
            "id": message_id,
            "subject": subject,
            "date": date,
            "status":label,
            "from": sender
        })

    runtime = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    # bucket_name = os.environ["BUCKET_NAME"]
    file_name = f"gmail_export_{runtime}.json"

    try:
        # Convert dictionary to a deployment-ready JSON string
        json_string = json.dumps(email_result)
        
        upload_to_volume(file_name, secretmanager_creds, json_string.encode("utf-8"))
        
        return {
            'statusCode': 200,
            'body': json.dumps('File uploaded successfully!')
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        raise e