import os
import tempfile
from diagrams import Diagram, Cluster, Edge
from diagrams.aws import compute as aws_compute, database as aws_database, network as aws_network, storage as aws_storage, integration as aws_integration, security as aws_security, analytics as aws_analytics, ml as aws_ml
from diagrams.gcp import compute as gcp_compute, database as gcp_database, network as gcp_network, storage as gcp_storage, analytics as gcp_analytics, ml as gcp_ml
from diagrams.azure import compute as azure_compute, database as azure_database, network as azure_network, storage as azure_storage, analytics as azure_analytics, ml as azure_ml
from diagrams.k8s import compute as k8s_compute, network as k8s_network, storage as k8s_storage
from diagrams.onprem import compute as onprem_compute, database as onprem_database, network as onprem_network, analytics as onprem_analytics
from diagrams.saas import analytics as saas_analytics, chat as saas_chat, identity as saas_identity

with Diagram("AI Credit Card Balance Payments - Infrastructure Diagram", show=False, filename="diagram", direction="TB"):
    with Cluster("AWS Core Services"):
        aws_apigw = aws_network.APIGateway("API Gateway (Public API + Webhooks)")
        aws_lambda_api = aws_compute.Lambda("API Lambda (Auth, Orchestration, Chatbot)")
        aws_lambda_worker = aws_compute.Lambda("Worker Lambda (Payments, Reconciliation)")
        aws_rds = aws_database.RDS("RDS (Postgres) - User profiles, transactions")
        aws_dynamodb = aws_database.Dynamodb("DynamoDB - Idempotency, sessions, rule-engine flags")
        aws_s3 = aws_storage.SimpleStorageServiceS3("S3 - Transaction exports, receipts, logs")
        aws_sqs = aws_integration.SimpleQueueServiceSqs("SQS - Task queue (payments, reminders)")
        aws_sns = aws_integration.SimpleNotificationServiceSns("SNS - Ops & alert fanout")
        aws_ec2 = aws_compute.EC2("EC2 - Legacy connectors / regional adapters")
    with Cluster("GCP ML & Webhook Processing"):
        gcp_functions_webhook = gcp_compute.Functions("Cloud Functions - Webhook & enrichment handlers")
        gcp_gce_ml = gcp_compute.ComputeEngine("GCE - Model training & inference (batch / real-time)")
        gcp_gcs = gcp_storage.Storage("GCS - Model artifacts & training data")
        gcp_firestore = gcp_database.Firestore("Firestore - Predictions cache & session recommendations")
        gcp_sql = gcp_database.SQL("Cloud SQL - Analytical store / feature exports")
        gcp_loadbalancer = gcp_network.LoadBalancing("Load Balancer (ML endpoints) ")
    with Cluster("Azure Scheduling & Regional Gateways"):
        azure_functions_scheduler = azure_compute.FunctionApps("Functions - Cron scheduler for reminders & retries")
        azure_vm_gateway = azure_compute.VM("VM Gateway - Regional/legacy issuer gateway")
        azure_storage = azure_storage.BlobStorage("Blob Storage - Backups / schedule logs")
        azure_loadbalancer = azure_network.LoadBalancers("Load Balancer (regional) ")
    with Cluster("On-Prem / Compliance Systems"):
        onprem_server_ops = onprem_compute.Server("Ops Manual Approval Portal (Human-in-loop)")
        onprem_postgresql = onprem_database.Postgresql("Postgres (Sensitive PII vault, compliance)")
    saas_auth0 = saas_identity.Auth0("Auth0 / OIDC Provider (OAuth, SCA flows)")
    saas_slack = saas_chat.Slack("Slack - Ops & Alerts")
    saas_teams = saas_chat.Teams("Microsoft Teams - Ops & Alerts")
    aws_apigw >> Edge(label="Token verification / OAuth introspect") >> saas_auth0
    aws_apigw >> Edge(label="Invoke REST -> Orchestration & Chatbot") >> aws_lambda_api
    aws_lambda_api >> Edge(label="Read/Write profiles & transaction records (Postgres)") >> aws_rds
    aws_lambda_api >> Edge(label="Idempotency keys, session store, rule flags") >> aws_dynamodb
    aws_lambda_api >> Edge(label="Store transaction exports, receipts, logs") >> aws_s3
    aws_lambda_api >> Edge(label="Enqueue payment tasks, reminders (at-least-once)") >> aws_sqs
    aws_lambda_api >> Edge(label="Forward inbound webhooks & enrichment") >> gcp_functions_webhook
    aws_sqs >> Edge(label="Trigger worker (task processor)") >> aws_lambda_worker
    aws_lambda_worker >> Edge(label="Send features for inference / training requests") >> gcp_gce_ml
    gcp_gce_ml >> Edge(label="Read / Write model artifacts & training data") >> gcp_gcs
    gcp_gce_ml >> Edge(label="Write predicted spend, suggested payment plans") >> gcp_firestore
    aws_s3 >> Edge(label="Periodic ETL / sync of historical exports (S3 -> GCS)") >> gcp_gcs
    gcp_functions_webhook >> Edge(label="Update prediction cache & session state") >> gcp_firestore
    gcp_firestore >> Edge(label="Read cached predictions & recommendations") >> aws_lambda_api
    azure_functions_scheduler >> Edge(label="Scheduled enqueue of reminders & retry jobs") >> aws_sqs
    azure_functions_scheduler >> Edge(label="Store schedule logs & backups") >> azure_storage
    aws_lambda_worker >> Edge(label="High-risk / manual-approval actions (human-in-loop)") >> onprem_server_ops
    onprem_server_ops >> Edge(label="Read/Write sensitive PII (compliance vault)") >> onprem_postgresql
    aws_lambda_api >> Edge(label="Secure sync of consented sensitive data (TLS/VPN)") >> onprem_postgresql
    aws_apigw >> Edge(label="Broadcast system alerts & critical events") >> aws_sns
    aws_sns >> Edge(label="Ops alerts -> Slack channels") >> saas_slack
    aws_sns >> Edge(label="Ops alerts -> Teams channels") >> saas_teams
    aws_lambda_api >> Edge(label="Operational alerts & manual approval messages") >> saas_slack
    aws_lambda_worker >> Edge(label="Fallback / regional legacy issuer integrations") >> azure_vm_gateway
    gcp_sql >> Edge(label="Analytical queries and feature extracts for training") >> gcp_gce_ml
    aws_rds >> Edge(label="Periodic analytics ETL export") >> gcp_sql
    aws_ec2 >> Edge(label="Legacy connector workers invoked by orchestration") >> aws_lambda_worker
    aws_lambda_worker >> Edge(label="Persist payment attempt logs & receipts") >> aws_s3
    onprem_server_ops >> Edge(label="Manual approval notifications to operators") >> saas_slack