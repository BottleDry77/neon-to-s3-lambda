import os
import boto3
import subprocess
import datetime
from urllib.parse import urlparse, parse_qs

# Load environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_PREFIX = os.getenv("S3_PREFIX", "dbBackup/")

# Ensure DATABASE_URL is provided
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")

# Parse the DATABASE_URL
def parse_database_url(db_url):
    """Parses the DATABASE_URL into components."""
    parsed_url = urlparse(db_url)
    query_params = parse_qs(parsed_url.query)

    return {
        "DB_HOST": parsed_url.hostname,
        "DB_NAME": parsed_url.path.lstrip("/"), 
        "DB_USER": parsed_url.username,
        "DB_PASSWORD": parsed_url.password,
        "DB_PORT": parsed_url.port if parsed_url.port else 5432,  # Default PostgreSQL port
        "SSL_MODE": query_params.get("sslmode", ["require"])[0]  # Default to require
    }

# Extract database connection details
db_config = parse_database_url(DATABASE_URL)

# AWS S3 Client
s3 = boto3.client("s3")

def lambda_handler(event, context):
    """Lambda function to backup Neon PostgreSQL database and upload to S3."""
    
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"postgres_backup_{timestamp}.sql.gz"
    local_backup_path = f"/tmp/{backup_filename}"
    
    try:
        # Run pg_dump with gzip compression & ensure SSL is enforced
        dump_command = (
            f"PGPASSWORD='{db_config['DB_PASSWORD']}' pg_dump "
            f"-h {db_config['DB_HOST']} "
            f"-U {db_config['DB_USER']} "
            f"-p {db_config['DB_PORT']} "
            f"-d {db_config['DB_NAME']} "
            f"--sslmode={db_config['SSL_MODE']} | gzip > {local_backup_path}"
        )
        
        # Run the command and capture output
        result = subprocess.run(dump_command, shell=True, check=True, text=True, executable="/bin/bash", capture_output=True)
        print("pg_dump output:", result.stdout)

        # Upload to S3
        s3.upload_file(local_backup_path, S3_BUCKET, f"{S3_PREFIX}{backup_filename}")
        
        print(f"Backup successfully uploaded: s3://{S3_BUCKET}/{S3_PREFIX}{backup_filename}")
        return {"status": "success", "file": f"s3://{S3_BUCKET}/{S3_PREFIX}{backup_filename}"}
    
    except subprocess.CalledProcessError as e:
        print(f"Backup failed: {e.stderr}")
        return {"status": "error", "message": str(e)}

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {"status": "error", "message": str(e)}
