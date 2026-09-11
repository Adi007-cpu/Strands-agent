import boto3

# Correct way for long-term IAM User Access Keys:
client = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1",
    aws_access_key_id="AK.........",
    aws_secret_access_key="PmCPm................",)
response = client.converse(
         modelId="openai.gpt-oss-120b-1:0", messages=[{"role": "user", "content": [{"text": 
    "Hello, are you working?"}]}], ) 
print(response["output"]["message"]["content"][0]["text"])


# Note: Do NOT include aws_session_token unless you are using temporary STS credentials.