import boto3
import subprocess
import zipfile
import os
import shutil

REGION = "us-east-1"
PROCESSED_BUCKET = "soccer-analytics-processed-dev"

# Clean previous builds
for path in ["package", "layer", "lambda.zip", "layer.zip"]:
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

# Install pandera layer
print("Installing pandera layer...")
layer_path = os.path.join("layer", "python")
os.makedirs(layer_path, exist_ok=True)
subprocess.run([
    "pip", "install", "pandera",
    "--target", layer_path,
    "--platform", "manylinux2014_x86_64",
    "--implementation", "cp",
    "--python-version", "3.11",
    "--only-binary=:all:",
    "--upgrade", "--quiet"
], check=True)

# Zip source files only
with zipfile.ZipFile("lambda.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for f in ["lambda_function.py", "transformer.py", "validator.py"]:
        z.write(f"src/{f}", f)
print("Packaged lambda.zip")

# Upload to S3
s3 = boto3.client("s3", region_name=REGION)
s3.upload_file("lambda.zip", PROCESSED_BUCKET, "lambda/lambda.zip")
print(f"Uploaded lambda.zip to s3://{PROCESSED_BUCKET}/lambda/lambda.zip")