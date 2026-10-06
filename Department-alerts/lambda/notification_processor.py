import json
import os
import time

try:
    import boto3  # type: ignore[import-not-found]
except ImportError:
    boto3 = None

# Initialize SES client using Boto3 when the dependency is available
if boto3 is not None:
    ses = boto3.client('ses')
    # Initialize the DynamoDB resource
    dynamodb = boto3.resource('dynamodb')
else:
    ses = None
    dynamodb = None

# Fetch configuration safely from Lambda Environment Variables
AUDIT_TABLE_NAME = os.environ.get('AUDIT_TABLE_NAME', 'Enterprise-Notification-Audit-Logs')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'no-reply@enterprise.com')
table = dynamodb.Table(AUDIT_TABLE_NAME) if dynamodb is not None else None

def load_template(filename):
    """Helper function to safely read HTML template files from the local directory."""
    # Looks for files in the same directory as this script
    file_path = os.path.join(os.path.dirname(__file__), filename)
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def lambda_handler(event, context):
    # 1. Initialize globally inside the handler to prevent UnboundLocalError
    recipient_email = "Unknown"
    try:
        # Pre-load templates into memory once per execution batch
        onboarding_html_raw = load_template('onboarding_alert.html')
        offboarding_html_raw = load_template('offboarding_alert.html')

        # Check if this function accidentally received an S3 event instead of SQS
        if 'Records' in event and 's3' in event['Records'][0]:
            print("WARNING: This Lambda function is being triggered directly by S3! It must be triggered by SQS.")
            return {'statusCode': 400, 'body': 'Wrong trigger structure.'}

        # AWS automatically groups SQS messages into 'Records' when triggering Lambda
        for record in event['Records']:
            # 1. Unpack the SQS message body payload
            message_payload = json.loads(record['body'])
            recipient_email = message_payload.get('recipient')
            recipient_name = message_payload.get('name', 'Valued Customer')
            status = message_payload.get('status', 'onboarding')
            
            print(f"Attempting to send email to {recipient_name} at {recipient_email}")
            
            if not recipient_email:
                continue
            print(f"Status of {recipient_name} is {status}")
            # Read and format the distinct template files
            if status == "offboarding":
                subject = "Application Status Update - Mail-Matrix: Stream"
                body_html = offboarding_html_raw.replace("{name}", recipient_name).replace("{year}", "2026")
            else:
                subject = "Employee Onboarding from Mail-Matrix: Stream"
                body_html = onboarding_html_raw.replace("{name}", recipient_name).replace("{year}", "2026")
            
            print(f"Dispatching {status} letter to {recipient_name} ({recipient_email})")
            
            # Deliver the processed HTML block via Amazon SES
            response = ses.send_email(
                Source = SENDER_EMAIL,
                Destination={
                        'ToAddresses': [recipient_email]
                        },
                Message={
                        'Subject': {
                        'Data': subject, 'Charset': 'UTF-8'
                        },
                        'Body': {
                        'Html': {
                            'Data': body_html, 'Charset': 'UTF-8'
                            }
                        }
                    }
                )
            ses_message_id = response['MessageId']
            print(f"Email sent to {recipient_email}! Message ID: {ses_message_id}")

            # WRITE AUDIT LOG TO DYNAMODB
            table.put_item(
                Item={
                    'message_id': ses_message_id,
                    'recipient_email': recipient_email,
                    'employee_name': recipient_name,
                    'lifecycle_status': status,
                    'timestamp': str(int(time.time())) # Epoch UNIX timestamp
                }
            )
            print(f"Audit log recorded in DynamoDB for {recipient_email}")
            
            
    except Exception as e:
        print(f"Error sending email to {recipient_email}: {str(e)}")
        raise e
    
    return {
        'statusCode': 200,
        'body': json.dumps('Processed SQS successfully!')
    }
