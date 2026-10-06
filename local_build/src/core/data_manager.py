# Refactored local_build/src/core/data_manager.py
import csv
import os

def load_recipients(file_path):
    file_path = os.path.abspath(file_path)
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return [row for row in reader]

def validate_recipients(recipients):
    for recipient in recipients:
        if not recipient.get('email'):
            raise ValueError("Data Validation Error: Missing 'email' attribute.")
    return True

if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    recipients_file = os.path.join(script_dir, '..', '..', 'data', 'employees_sample.csv')
    try:
        data = load_recipients(recipients_file)
        validate_recipients(data)
        print("Data architecture validation: PASSED")
    except Exception as e:
        print(f"Data architecture validation: FAILED -> {e}")
