# Home Automation AWS Lambda Functions

This repository contains a collection of AWS Lambda functions for personal automation tasks. Each function is designed to run on a schedule and provide notifications for different use cases.

## Current Automation Functions

1. **Temperature Notification** - Sends alerts when temperature drops below a threshold
2. **Loto Price Checker** - *(Coming soon)* - Will check and notify about lottery prize amounts

## Project Structure
- `/src/` - Contains source code for each Lambda function
  - `/src/lambda_temperature_notification/` - Temperature notification function
  - `/src/lambda_loto_price_checker/` - *(Coming soon)* Loto price checker function
- `/terraform/` - Contains Terraform infrastructure as code to deploy resources to AWS

## Terraform Deployment

This project uses Terraform to automate the deployment of all required AWS resources. The Terraform configuration creates all necessary resources for each Lambda function, including:

1. **Lambda Functions** with all required dependencies
2. **IAM Roles** with appropriate permissions
3. **DynamoDB Tables** for data persistence
4. **SNS Topics** for notifications
5. **CloudWatch Event Rules** for scheduling
6. **CloudWatch Log Groups** for logging

### Steps to Deploy with Terraform

1. **Configure Variables**
   - Update `/terraform/terraform.tfvars` with your specific values
   - See individual function READMEs for required variables

2. **Initialize Terraform**
   ```
   cd terraform
   terraform init
   ```

3. **Preview Changes**
   ```
   terraform plan
   ```

4. **Apply Configuration**
   ```
   terraform apply
   ```

### Cleanup Resources
To remove all AWS resources created by this project:
```
cd terraform
terraform destroy
```

## Function-Specific Documentation

For detailed information about each function, refer to their respective README files:

- [Temperature Notification README](/src/lambda_temperature_notification/README.md)
- Loto Price Checker README *(Coming soon)*

## AWS Free Tier Usage

All functions in this repository are designed to work within AWS Free Tier limits when possible. Costs are minimal for personal use cases and are detailed in each function's documentation.
