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

### **Neon PostgreSQL Credentials (DATABASE_URL)**
Neon provides a **DATABASE_URL** containing all necessary connection details (host, user, password, database).

- **Example Non-Pooled DATABASE_URL:**
postgresql://<USERNAME>:<PASSWORD>@<HOSTNAME>/<DATABASE>?sslmode=require

pgsql
Copy
Edit

⚠ **Important Notes:**  
- Use the **"Non-Pooled"** connection string for backups.  
- **Ensure `"sslmode=require"` is present** for a secure connection.  
- The full **DATABASE_URL should be stored in the Lambda environment variables** under `DATABASE_URL` in the AWS Lambda console.

---

# 🚀 **Initial Deployment (For New Users)**  
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
2️⃣ Set Environment Variables

aws lambda update-function-configuration \
  --function-name NeonDBBackup \
  --environment "Variables={DATABASE_URL=<your-neon-db-url>,S3_BUCKET=<your-s3-bucket>,S3_PREFIX=dbBackup/}"
3️⃣ Trigger the Function Manually

sh
Copy
Edit
aws lambda invoke --function-name NeonDBBackup response.json
✅ Your Lambda function is now deployed and will back up your Neon PostgreSQL database to S3.



Option 2: Build and Deploy Your Own ECR Image
(If you prefer to build and push your own Docker image instead of using the public one.)

1️⃣ Clone this Repository

git clone https://github.com/<your-repo>/neon-db-backup-lambda.git
cd neon-db-backup-lambda
2️⃣ Build the Docker Image

docker build -t neon-db-backup .
3️⃣ Authenticate Docker with AWS ECR

aws ecr get-login-password --region <aws-region> | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.<aws-region>.amazonaws.com
4️⃣ Tag and Push to ECR

docker tag neon-db-backup:latest <AWS_ACCOUNT_ID>.dkr.ecr.<aws-region>.amazonaws.com/neon-db-backup:latest
docker push <AWS_ACCOUNT_ID>.dkr.ecr.<aws-region>.amazonaws.com/neon-db-backup:latest
5️⃣ Create the Lambda Function

aws lambda create-function \
  --function-name NeonDBBackup \
  --package-type Image \
  --code ImageUri=<AWS_ACCOUNT_ID>.dkr.ecr.<aws-region>.amazonaws.com/neon-db-backup:latest \
  --role <IAM_ROLE_ARN>
6️⃣ Set Environment Variables

aws lambda update-function-configuration \
  --function-name NeonDBBackup \
  --environment "Variables={DATABASE_URL=<your-neon-db-url>,S3_BUCKET=<your-s3-bucket>,S3_PREFIX=dbBackup/}"
7️⃣ Trigger the Function Manually

aws lambda invoke --function-name NeonDBBackup response.json
✅ Your Lambda function is now deployed and ready to use!

🔄 Updating an Existing Deployment
(For users who have already deployed the Lambda function and need to update it.)

Option 1: Using the Public ECR Image
(Once available, replace <public-ecr-url> with the correct URI)

aws lambda update-function-code \
  --function-name NeonDBBackup \
  --image-uri <public-ecr-url>:latest
Option 2: Pushing an Updated Custom Image
1️⃣ Modify lambda_function.py

Apply your changes to lambda_function.py
Save the file.
2️⃣ Rebuild the Docker Image

sh
Copy
Edit
docker build -t neon-db-backup .
3️⃣ Tag and Push the Updated Image

docker tag neon-db-backup:latest <AWS_ACCOUNT_ID>.dkr.ecr.<aws-region>.amazonaws.com/neon-db-backup:latest
docker push <AWS_ACCOUNT_ID>.dkr.ecr.<aws-region>.amazonaws.com/neon-db-backup:latest
4️⃣ Update the Lambda Function

aws lambda update-function-code \
  --function-name NeonDBBackup \
  --image-uri <AWS_ACCOUNT_ID>.dkr.ecr.<aws-region>.amazonaws.com/neon-db-backup:latest
5️⃣ Verify Deployment

aws lambda get-function-configuration --function-name NeonDBBackup --query "Code.ImageUri"
6️⃣ Invoke the Function

aws lambda invoke --function-name NeonDBBackup response.json
7️⃣ Check CloudWatch Logs for Errors

aws logs tail /aws/lambda/NeonDBBackup --follow
📁 Checking Backup Files in S3
After a successful run, backups should appear in S3.
To list them:

aws s3 ls s3://<your-s3-bucket>/<your-s3-prefix> --human-readable --summarize





