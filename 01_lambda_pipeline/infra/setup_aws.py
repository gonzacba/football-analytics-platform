import boto3
import zipfile
import os
import json
import time

REGION = "us-east-1"
RAW_BUCKET = "soccer-raw-events-gonvi"
PROCESSED_BUCKET = "soccer-processed-gonvi"
LAMBDA_NAME = "soccer-event-pipeline"
ROLE_NAME = "soccer-lambda-role"

def create_buckets():
    s3 = boto3.client("s3", region_name=REGION)
    for bucket in [RAW_BUCKET, PROCESSED_BUCKET]:
        s3.create_bucket(Bucket=bucket)
        print(f"✓ Created bucket: {bucket}")

def create_lambda_role():
    iam = boto3.client("iam")
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    role = iam.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(trust_policy)
    )
    iam.attach_role_policy(
        RoleName=ROLE_NAME,
        PolicyArn="arn:aws:iam::aws:policy/AmazonS3FullAccess"
    )
    iam.attach_role_policy(
        RoleName=ROLE_NAME,
        PolicyArn="arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
    )
    print(f"✓ Created IAM role: {ROLE_NAME}")
    return role["Role"]["Arn"]

def package_lambda():
    import shutil

    # Clean previous builds
    for path in ["package", "layer", "lambda.zip", "layer.zip"]:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

    # Install only pandera (small) into a slim layer
    print("Installing pandera into slim layer...")
    layer_path = os.path.join("layer", "python")
    os.makedirs(layer_path, exist_ok=True)
    import subprocess
    subprocess.run([
        "pip", "install", "pandera",
        "--target", layer_path,
        "--platform", "manylinux2014_x86_64",
        "--implementation", "cp",
        "--python-version", "3.11",
        "--only-binary=:all:",
        "--upgrade",
        "--quiet"
    ], check=True)

    # Zip the layer
    with zipfile.ZipFile("layer.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk("layer"):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, "layer")
                z.write(file_path, arcname)
    size_mb = os.path.getsize("layer.zip") / (1024 * 1024)
    print(f"✓ Packaged layer.zip ({size_mb:.1f} MB)")

    # Zip only source files for Lambda
    with zipfile.ZipFile("lambda.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in ["lambda_function.py", "transformer.py", "validator.py"]:
            z.write(f"src/{f}", f)
    print("✓ Packaged lambda.zip (source only)")


def deploy_lambda(role_arn):
    print("Uploading packages to S3...")
    s3 = boto3.client("s3", region_name=REGION)
    s3.upload_file("layer.zip", PROCESSED_BUCKET, "lambda/layer.zip")
    s3.upload_file("lambda.zip", PROCESSED_BUCKET, "lambda/lambda.zip")
    print("✓ Uploaded packages to S3")

    print("Waiting for IAM role to propagate...")
    time.sleep(15)

    lam = boto3.client("lambda", region_name=REGION)

    # Publish pandera layer
    layer_response = lam.publish_layer_version(
        LayerName="soccer-dependencies",
        Content={
            "S3Bucket": PROCESSED_BUCKET,
            "S3Key": "lambda/layer.zip"
        },
        CompatibleRuntimes=["python3.11"],
        CompatibleArchitectures=["x86_64"]
    )
    pandera_layer_arn = layer_response["LayerVersionArn"]
    print("✓ Published pandera layer")

    # Use AWS public pandas layer (maintained by AWS, includes pandas + pyarrow)
    # This is the official AWS Data Wrangler / SDK for pandas layer
    pandas_layer_arn = "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python311:24"
    print("✓ Using AWS public pandas+pyarrow layer")

    # Deploy Lambda with both layers
    lam.create_function(
        FunctionName=LAMBDA_NAME,
        Runtime="python3.11",
        Role=role_arn,
        Handler="lambda_function.handler",
        Code={
            "S3Bucket": PROCESSED_BUCKET,
            "S3Key": "lambda/lambda.zip"
        },
        Layers=[pandas_layer_arn, pandera_layer_arn],
        Environment={"Variables": {"OUTPUT_BUCKET": PROCESSED_BUCKET}},
        Timeout=60,
        MemorySize=512
    )
    print(f"✓ Deployed Lambda: {LAMBDA_NAME}")

def add_s3_trigger():
    print("Waiting for Lambda to be ready...")
    time.sleep(15)
    lam = boto3.client("lambda", region_name=REGION)
    s3 = boto3.client("s3", region_name=REGION)
    account_id = boto3.client("sts").get_caller_identity()["Account"]

    # Give S3 permission to invoke Lambda
    lam.add_permission(
        FunctionName=LAMBDA_NAME,
        StatementId="S3InvokeLambda",
        Action="lambda:InvokeFunction",
        Principal="s3.amazonaws.com",
        SourceArn=f"arn:aws:s3:::{RAW_BUCKET}"
    )

    # Add S3 event notification
    s3.put_bucket_notification_configuration(
        Bucket=RAW_BUCKET,
        NotificationConfiguration={
            "LambdaFunctionConfigurations": [{
                "LambdaFunctionArn": f"arn:aws:lambda:{REGION}:{account_id}:function:{LAMBDA_NAME}",
                "Events": ["s3:ObjectCreated:*"],
                "Filter": {
                    "Key": {
                        "FilterRules": [
                            {"Name": "prefix", "Value": "raw/"},
                            {"Name": "suffix", "Value": ".json"}
                        ]
                    }
                }
            }]
        }
    )
    print(f"✓ S3 trigger configured on {RAW_BUCKET}")

if __name__ == "__main__":
    print("=== Deploying soccer Analytics Pipeline ===")
    create_buckets()
    role_arn = create_lambda_role()
    package_lambda()
    deploy_lambda(role_arn)
    add_s3_trigger()
    print("\n=== Deployment Complete ===")
    print(f"Upload JSON files to s3://{RAW_BUCKET}/raw/ to trigger the pipeline")