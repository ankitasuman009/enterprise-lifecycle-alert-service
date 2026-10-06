import json
import boto3
import csv
import io
import os

# Initialize both S3 and SQS clients using Boto3
s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')


QUEUE_URL = os.environ.get('NOTIFICATION_QUEUE_URL', 'https://sqs.ap-southeast-2.amazonaws.com/123456789012/SQSQueue')

def lambda_handler(event, context):
    
    try:
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        file_key = event['Records'][0]['s3']['object']['key']
    except KeyError as e:
        print(f"Error extracting event data: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps('Error extracting event data.')
        }
    
    
    try:
        # fetching the CSV file from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        csv_content = response['Body'].read().decode('utf-8')
        
        print("CSV Content:", csv_content)
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        
         # Loop through lines and push targets to SQS
        pushed_count = 0
        for row in reader:
            try: 
                print("Row Data:", row)
                # recipient = row['email']  
                recipient = row.get('email')
                name = row.get('name', 'Valued Customer')
                # Extract status, default to 'onboarding' if left blank safely
                status = row.get('status', 'onboarding').strip().lower() 

                # Create a structured message payload
                if recipient:
                    message_body = {
                        'recipient': recipient.strip(),
                        'name': name.strip(),
                        'status': status
                    }

                    # Push the individual payload into the SQS Queue
                    sqs_client.send_message(
                        QueueUrl=QUEUE_URL,
                        MessageBody=json.dumps(message_body)
                    )
                    pushed_count += 1
            except KeyError as e:
                print(f"Skipping malformed row block: {e}")
        print(f"Successfully buffered and queued {pushed_count} transactions into SQS downstream pipeline.")
        return {'statusCode': 200, 'body': f"Buffered {pushed_count} pipeline alerts."}
    
    
    except Exception as e:
        print(f"Transactional processing failure on storage object: {str(e)}")
        return {'statusCode': 500, 'body': 'Internal execution subsystem error.'}
        
