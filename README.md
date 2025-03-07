# neon-to-s3-lambda
AWS Lambda function for automated Neon.tech PostgreSQL backups to Amazon S3 using Docker.

# **AWS Lambda PostgreSQL Backup - Deployment Guide**

## **Overview**
This project automates **PostgreSQL database backups** from **Neon.tech** to **AWS S3** using:
- **AWS Lambda (Docker-based)**
- **Amazon ECR (Container Registry)**
- **AWS S3 (Storage)**
- **AWS EventBridge (Scheduled Execution)**

This guide covers **initial deployment** and **updating** an existing deployment.

---

## **Prerequisites**
Ensure you have the following installed and configured:

✅ **AWS Credentials** (IAM permissions for Lambda, S3, and ECR)  
✅ **Docker** (for testing and building the Lambda container)  
✅ **AWS CLI** (for deploying and managing AWS resources)  
✅ **S3 Bucket** (where backups will be stored)  
✅ **S3 Prefix** *(optional, defaults to `"dbBackup/"` if not defined.)*  
✅ **Neon PostgreSQL Connection String** (DATABASE_URL)
✅ **Update <your-s3-bucket> in S3-policy.json with S3 Bucket name**    

### **Neon PostgreSQL Credentials (DATABASE_URL)**
Neon provides a **DATABASE_URL** containing all necessary connection details (host, user, password, database).

- **Example Non-Pooled DATABASE_URL:**
```sh
postgresql://<USERNAME>:<PASSWORD>@<HOSTNAME>/<DATABASE>?sslmode=require
```

⚠ **Important Notes:**  
- Use the **"Non-Pooled"** connection string for backups.  
- **Ensure `"sslmode=require"` is present** for a secure connection.  
- The full **DATABASE_URL should be stored in the Lambda environment variables** under `DATABASE_URL`.
  (AWS Systems Manager Parameter Store and AWS Secrets Manager are alternative options for securely storing credentials but are not discussed here.)

---

# **Creating the IAM Role**
```sh
aws iam create-role --role-name LambdaNeonBackupRole --assume-role-policy-document file://trust-policy.json
```
Attach Policies

```sh
aws iam attach-role-policy --role-name LambdaNeonBackupRole --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
```
```sh
aws iam put-role-policy --role-name LambdaNeonBackupRole --policy-name S3BackupPolicy --policy-document file://s3-policy.json
```
```sh
aws iam attach-role-policy --role-name LambdaNeonBackupRole --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
```


---

# 🚀 **Initial Deployment**  
*(If you are already using the Lambda function and only need to update it, skip to the next section.)*  

### **Option 1: Using the Public ECR Image (Recommended)**
*(Once available, replace `<public-ecr-url>` with the correct URI)*  

1️⃣ **Create the Lambda Function**  
```sh
aws lambda create-function \
--function-name NeonDBBackup \
--package-type Image \
--code ImageUri=<public-ecr-url>:latest \
--role <IAM_ROLE_ARN>
```
2️⃣ Set Environment Variables
```sh
aws lambda update-function-configuration \
  --function-name NeonDBBackup \
  --environment "Variables={DATABASE_URL=<your-neon-db-url>,S3_BUCKET=<your-s3-bucket>,S3_PREFIX=dbBackup/}"
```
3️⃣ Trigger the Function Manually
```sh
aws lambda invoke --function-name NeonDBBackup response.json
✅ Your Lambda function is now deployed and will back up your Neon PostgreSQL database to S3.
```


### **Option 2: Build and Deploy Your Own ECR Image**
(If you prefer to build and push your own Docker image instead of using the public one.)

1️⃣ Clone this Repository
```sh
git clone https://github.com/<your-repo>/neon-db-backup-lambda.git
cd neon-db-backup-lambda
```
2️⃣ Build the Docker Image
```sh
docker build -t neon-db-backup .
```
3️⃣ Authenticate Docker with AWS ECR
```sh
aws ecr get-login-password --region <aws-region> | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.<aws-region>.amazonaws.com
```
4️⃣ Tag and Push to ECR
```sh
docker tag neon-db-backup:latest <AWS_ACCOUNT_ID>.dkr.ecr.<aws-region>.amazonaws.com/neon-db-backup:latest
docker push <AWS_ACCOUNT_ID>.dkr.ecr.<aws-region>.amazonaws.com/neon-db-backup:latest
```
5️⃣ Create the Lambda Function
```sh
aws lambda create-function \
  --function-name NeonDBBackup \
  --package-type Image \
  --code ImageUri=<AWS_ACCOUNT_ID>.dkr.ecr.<aws-region>.amazonaws.com/neon-db-backup:latest \
  --role <IAM_ROLE_ARN>
```
6️⃣ Set Environment Variables
```sh
aws lambda update-function-configuration \
  --function-name NeonDBBackup \
  --environment "Variables={DATABASE_URL=<your-neon-db-url>,S3_BUCKET=<your-s3-bucket>,S3_PREFIX=dbBackup/}"
```
7️ Attach IAM Role to Lambda
```sh
aws lambda update-function-configuration --function-name NeonDBBackup --role arn:aws:iam::<AWS_ACCOUNT_ID>:role/LambdaNeonBackupRole
```

8️⃣ Trigger the Function Manually
```sh
aws lambda invoke --function-name NeonDBBackup response.json
```
✅ Your Lambda function is now deployed and ready to use!

---
# 🔄 **Updating an Existing Deployment**
*(For users who have already deployed the their own Docker-Lambda function and need to update it.)*

**Pushing an Updated Custom Image**

1️⃣ Modify lambda_function.py

Apply your changes to lambda_function.py
Save the file.

2️⃣ Rebuild the Docker Image
```sh
docker build -t neon-db-backup .
```
3️⃣ Tag and Push the Updated Image
```sh
docker tag neon-db-backup:latest <AWS_ACCOUNT_ID>.dkr.ecr.<aws-region>.amazonaws.com/neon-db-backup:latest
docker push <AWS_ACCOUNT_ID>.dkr.ecr.<aws-region>.amazonaws.com/neon-db-backup:latest
```
4️⃣ Update the Lambda Function
```sh
aws lambda update-function-code \
  --function-name NeonDBBackup \
  --image-uri <AWS_ACCOUNT_ID>.dkr.ecr.<aws-region>.amazonaws.com/neon-db-backup:latest
```
5️⃣ Verify Deployment
```sh
aws lambda get-function-configuration --function-name NeonDBBackup --query "Code.ImageUri"
```
6️⃣ Invoke the Function
```sh
aws lambda invoke --function-name NeonDBBackup response.json
```
7️⃣ Check CloudWatch Logs for Errors
```sh
aws logs tail /aws/lambda/NeonDBBackup --follow
```

---

***📁 Checking Backup Files in S3***
After a successful run, backups should appear in S3.
To list them:
```sh
aws s3 ls s3://<your-s3-bucket>/<your-s3-prefix> --human-readable --summarize
```
---
#⏳ **Automating Backups with EventBridge**
🔹 Step 1: Create a New EventBridge Rule
```sh
aws events put-rule \
  --name NeonDBBackupSchedule \
  --schedule-expression "rate(24 hours)"
```
🔹 Step 2: Grant EventBridge Permission to Invoke Lambda
```sh
aws lambda add-permission \
  --function-name NeonDBBackup \
  --statement-id EventBridgeInvoke \
  --action "lambda:InvokeFunction" \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:<aws-region>:<aws-account-id>:rule/NeonDBBackupSchedule
```
🔹 Step 3: Attach the Rule to the Lambda Function
```sh
aws events put-targets \
  --rule NeonDBBackupSchedule \
  --targets "Id"="1","Arn"="arn:aws:lambda:<aws-region>:<aws-account-id>:function:NeonDBBackup"
  ```
✅ Done!
To verify, list existing rules:
```sh
aws events list-rules
```