import boto3

REGION = "us-east-1"
LAMBDA_NAME = "football-event-pipeline"
ROLE_NAME = "football-lambda-role"

lam = boto3.client("lambda", region_name=REGION)
try:
    lam.delete_function(FunctionName=LAMBDA_NAME)
    print("Deleted Lambda")
except Exception as e:
    print(f"Lambda: {e}")

iam = boto3.client("iam")
for policy in ["AmazonS3FullAccess", "CloudWatchLogsFullAccess"]:
    try:
        iam.detach_role_policy(RoleName=ROLE_NAME, PolicyArn=f"arn:aws:iam::aws:policy/{policy}")
    except:
        pass
try:
    iam.delete_role(RoleName=ROLE_NAME)
    print("Deleted IAM role")
except Exception as e:
    print(f"Role: {e}")

s3 = boto3.client("s3", region_name=REGION)
for bucket in ["football-raw-events-gonvi", "football-processed-gonvi"]:
    try:
        s3.delete_bucket(Bucket=bucket)
        print(f"Deleted bucket: {bucket}")
    except Exception as e:
        print(f"Bucket {bucket}: {e}")