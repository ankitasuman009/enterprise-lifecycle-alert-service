# Refactored local_build/src/cli/cli_tool.py
import argparse
import os
from core.data_manager import load_recipients
from core.template_manager import render_template
from email_sender import send_alert_notification 

def main():
    parser = argparse.ArgumentParser(description='Enterprise Lifecycle Notification CLI Ingestor Engine.')
    parser.add_argument('--data', required=True, help='Path to personnel records CSV file')
    parser.add_argument('--template', required=True, help='HTML template file identifier')
    parser.add_argument('--subject', required=True, help='Notification header string')
    args = parser.parse_args()

    recipients = load_recipients(args.data)
    template_file = os.path.basename(args.template)

    for recipient in recipients:
        email = recipient['email']
        context = {"name": recipient.get('name', 'Employee'), "year": "2026"}
        body = render_template(template_file, context) 
        response = send_alert_notification(email, args.subject, body)
        print(f"CLI Pipeline Stream -> Dispatched to {email}. ID: {response['MessageId']}")

if __name__ == "__main__":
    main()
