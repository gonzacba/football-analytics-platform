import boto3

REGION = "us-east-1"
LAMBDA_NAME = "soccer-event-pipeline"
ROLE_NAME = "soccer-lambda-role"
BUCKETS = ["soccer-raw-events-gonvi", "soccer-processed-gonvi"]

# Delete Lambda
lam = boto3.client("lambda", region_name=REGION)
try:
    lam.delete_function(FunctionName=LAMBDA_NAME)
    print("Deleted Lambda")
except Exception as e:
    print(f"Lambda: {e}")

# Detach policies and delete role
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

# Empty and delete buckets
s3 = boto3.client("s3", region_name=REGION)
for bucket in BUCKETS:
    try:
        # Delete all objects first
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket):
            objects = page.get("Contents", [])
            if objects:
                s3.delete_objects(
                    Bucket=bucket,
                    Delete={"Objects": [{"Key": o["Key"]} for o in objects]}
                )
        # Now delete the empty bucket
        s3.delete_bucket(Bucket=bucket)
        print(f"Deleted bucket: {bucket}")
    except Exception as e:
        print(f"Bucket {bucket}: {e}")