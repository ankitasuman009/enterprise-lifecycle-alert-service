# Enterprise Lifecycle Notification Service

An automated, serverless event-driven microservice designed to handle high-throughput, cross-department notifications during employee onboarding and offboarding phases. 

This repository leverages Amazon S3, AWS Lambda, Amazon SQS, Amazon SES, and Amazon DynamoDB to replace a high-latency, synchronous legacy architecture with a decoupled, asynchronous event stream that eliminates database throttling and execution timeouts.

## System Architecture


        [Corporate CSV Upload] ──> [Amazon S3 Bucket]
                             │
                             ▼ (S3 Object Created Event)
                    [Ingestion Lambda]
                             │
                             ▼ (Asynchronous Decoupling)
        [Amazon SQS Queue] <── [Dead Letter Queue (DLQ)]
                             │
                             ▼ (Managed Batch Triggers)
                    [Processor Lambda]
                             │
    ┌────────────────────────┴────────────────────────┐
    ▼                                                 ▼
    [Amazon SES Service]                             [Amazon DynamoDB]
    (Dispatches HTML Alerts to Managers)             (Persists Compliance Audit Logs)

## Why This Architecture?

In the legacy monolithic architecture, employee lifestyle status updates triggered synchronous loops that evaluated business logic and executed third-party API calls over a single connection block. Under peak concurrent loads, this introduced significant performance bottlenecks:
- **Database Throttling:** Massive write/read locks on core employee databases during batch iterations.
- **Connection Timeouts:** HTTP gateway drops due to long-running synchronous threads awaiting delivery receipts.

### The Serverless Solution:
- **Storage-Based Ingestion (S3):** Decouples input ingestion from compute processes. Large-scale CSV transactional records are written directly to distributed object storage.
- **Asynchronous Buffering (SQS):** Absorbs burst traffic and separates processing workloads from ingestion speeds. Isolates intermittent failures with an integrated Dead Letter Queue (DLQ).
- **Compute Scale (Lambda):** Leverages ephemeral compute scaling to process payload micro-batches simultaneously without server overhead.
- **Compliance Audit Trail (DynamoDB):** Provides a high-throughput, structured data store to maintain transaction verification histories for security and audit logs.

## Repository Structure

```bash
.
├── README.md
├── requirements.txt
├── package.json
├── architecture_diagram.png
├── templates/
│   ├── onboarding_alert.html
│   └── offboarding_alert.html
├── aws_lambda/
│   ├── s3_batch_ingestor.py        # Ingests storage triggers & buffers to SQS
│   └── notification_processor.py   # Processes SQS events & executes SES/DynamoDB
└── local_simulation/
    ├── data/
    │   └── employees_sample.csv
    └── src/
        └── local_processor_stub.py
```

## Production Cloud Workflow
The microservice models real-world enterprise infrastructure utilizing two decoupled execution tiers:

### 1. Ingestion Layer (`s3_batch_ingestor.py`)
Triggered automatically via an S3 `ObjectCreated` event mapping. It streams the data block, processes CSV rows line-by-line, and packages them into standard JSON notification payloads:
```json
{
  "recipient": "reporting-manager@enterprise.com",
  "name": "Alex Rivera",
  "status": "onboarding"
}
```
This payload is instantly published to Amazon SQS, allowing the S3 connection to close securely within milliseconds.

### 2. Processing & Dispatch Layer (`notification_processor.py`)

Triggered by incoming batches from SQS. It consumes the messages, maps the `status` attribute to corresponding business logic strings, compiles HTML structures dynamically, and dispatches critical operational updates to designated reporting managers via Amazon SES. 

Upon dispatch verification, transaction metadata is committed to Amazon DynamoDB:
- `message_id` (Primary Hash Key)
- `recipient_email`
- `employee_name`
- `lifecycle_status`
- `timestamp` (Unix Epoch)

## Local Development & Simulation

### Prerequisites
- Python 3.9+
- AWS SDK for Python (`boto3`)
- Standard AWS CLI profiles configured with isolated IAM permissions

### Installation & Environment Configuration
Clone the repository and install dependencies:
```bash
pip install -r requirements.txt
```

Set up global runtime configurations via environment variables instead of hardcoding system attributes:
```bash
export NOTIFICATION_QUEUE_URL=""
export AUDIT_TABLE_NAME="Enterprise-Notification-Audit-Logs"
export SENDER_EMAIL="no-reply@enterprise.com"
```
## Security & Architectural Best Practices
- **Least-Privilege Access (IAM):** Execution roles are scoped tightly; the ingestion function has write-only SQS privileges, while the processor holds read-only SQS and write-only DynamoDB permissions.
- **Environment Decoupling:** Credentials, queue targets, and table names are isolated completely into environment variables to preserve secure pipeline migrations across Staging and Production.
- **Fault-Tolerant Dead Letter Queue:** Unprocessable or corrupted records are diverted gracefully to a dedicated SQS DLQ after 3 retries, preserving stream integrity and facilitating deep debugging.
