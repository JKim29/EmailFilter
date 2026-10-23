import json
import boto3
from datetime import datetime, UTC

s3_client = boto3.client('s3')


def lambda_handler(event, context):
    test_data = {
        "header": "PBTech",
        "status": "Unread",
        "from": "@pbtech.co.nz"
    }

    runtime = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    bucket_name = "jk-email-dev-s3-bucket"
    file_name = f"gmail_export_{runtime}.json"

    try:
        # Convert dictionary to a deployment-ready JSON string
        json_string = json.dumps(test_data)
        
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