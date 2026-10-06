# Refactored local_build/src/email_sender.py
import boto3
import os
from core.data_manager import load_recipients
from core.template_manager import render_template

AWS_REGION = os.getenv('AWS_REGION', 'ap-southeast-2')
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'no-reply@enterprise.com')

client = boto3.client('ses', region_name=AWS_REGION)

def send_alert_notification(recipient_email, subject, body):
    return client.send_email(
        Source=SENDER_EMAIL,
        Destination={'ToAddresses': [recipient_email]},
        Message={
            'Subject': {'Data': subject},
            'Body': {'Html': {'Data': body}}
        }
    )

def main():
    recipients_file = os.getenv('RECIPIENTS_FILE_PATH', 'data/employees_sample.csv')
    recipients = load_recipients(recipients_file)
    
    for recipient in recipients:
        email = recipient['email']
        status = recipient.get('status', 'onboarding')
        context = {"name": recipient.get('name', 'Employee'), "year": "2026"}
        
        if status == "offboarding":
            subject = "Internal Corporate Alert: Employee Offboarding Scheduled"
            template_name = "offboarding_alert.html"
        else:
            subject = "Internal Corporate Alert: Employee Onboarding Access Granted"
            template_name = "onboarding_alert.html"
            
        body = render_template(template_name, context)
        response = send_alert_notification(email, subject, body)
        print(f"Lifecycle notification sent to {email}! Ticket ID: {response['MessageId']}")

if __name__ == "__main__":
    main()
