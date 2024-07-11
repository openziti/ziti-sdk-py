# Ziti S3 Log Uploader

This example shows how to upload *.log files to a private S3 bucket.

## Setup :wrench:

Refer to the [examples README](../README.md) for details on setting up a service and endpoint identities.

The rest of the example commands assume you are inside this example's directory.

```bash
cd ./samples/s3z
```

### Install Python Requirements

Install the PyPi modules required by this example.

```bash
pip install --requirement ./requirements.txt
```

## Set Up AWS

Here are the AWS ingredients.

1. Choose an AWS region to set everything up
1. An S3 VPC Endpoint (Privatelink Interface)
1. An S3 Bucket
1. A Bucket Policy that requires the VPCE source
1. A Security Group that allows the bucket service host to send 443/tcp to the VPCE
1. Any IAM credential

### Bucket Policy Example

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Deny-access-if-not-VPCE",
            "Effect": "Deny",
            "Principal": "*",
            "Action": [
                "s3:ListBucket",
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::boto-demo-s3z",
                "arn:aws:s3:::boto-demo-s3z/*"
            ],
            "Condition": {
                "StringNotEquals": {
                    "aws:sourceVpce": "vpce-0f3e9a76e6d070f9a"
                }
            }
        },
        {
            "Sid": "Allow-access-if-VPCE",
            "Effect": "Allow",
            "Principal": "*",
            "Action": [
                "s3:ListBucket",
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::boto-demo-s3z",
                "arn:aws:s3:::boto-demo-s3z/*"
            ],
            "Condition": {
                "StringEquals": {
                    "aws:sourceVpce": "vpce-0f3e9a76e6d070f9a"
                }
            }
        }
    ]
}
```

### AWS Credential

Any valid credential will work if your bucket policy requires only the VPC endpoint source. The AWS Python SDK (boto)
uses the same credential discovery as the `aws` CLI, so you can configure a credential with standard AWS environment
variables, shared credentials file, EC2 introspection API, etc.

## Set Up Ziti

Here are the Ziti ingredients.

1. A bucket service to configure the S3 endpoint URL
    1. `intercept.v1` - this configures the Python SDK client to send requests matching the VPC endpoint through the tunnel

      ```json
      {
        "addresses": [
          "*.vpce-0f3e9a76e6d070f9a.s3.us-west-1.vpce.amazonaws.com"
        ],
        "portRanges": [
          {
            "high": 443,
            "low": 443
          }
        ],
        "protocols": [
          "tcp"
        ]
      }
      ```

    1. `host.v1` - this configures the hosting endpoint to send the traffic exiting the Ziti tunnel to the VPC endpoint

      ```json
      {
        "address": "bucket.vpce-0f3e9a76e6d070f9a.s3.us-west-1.vpce.amazonaws.com",
        "allowedPortRanges": [
          {
            "high": 443,
            "low": 443
          }
        ],
        "allowedProtocols": [
          "tcp"
        ],
        "forwardPort": true,
        "forwardProtocol": true,
        "protocol": "tcp"
      }
      ```

1. Enrolled Ziti identities for each end of the tunnel
    1. client - `s3z.py` will use this identity to "dial" the bucket service
    1. host - a container or VM inside the VPC will provide a privileged exit point to the private endpoint, i.e., hosting tunneler

1. Service Policies
    1. Dial - the client identity needs dial permission for the bucket service
    1. Bind - the host needs bind permission for the bucket service

1. Router Policies - ensure your identities and services are granted access to at least one common, online router

## Generate Some Dummy Files

Generate some log files to upload if you need some.

```bash
python ./log-generator.py
```

## Understanding the Inputs :brain:

This example accepts some options and arguments.

1. `--ziti-identity-file` - The identity file to be used by the SDK tunneler to dial the bucket service
1. `--bucket-name` - where to upload log files
1. `--bucket-endpoint` - the private VPC endpoint URL
1. `--push-log-dir` - local directory where logs should be uploaded from
1. `--object-prefix` - optional directory-like prefix for the uploaded files

## Running the Example :arrow_forward:

```bash
python ./s3z/s3z.py \
  --ziti-identity-file=/etc/ziti/client.json \
  --bucket-name=my-private-logs \
  --bucket-endpoint=https://bucket.vpce-0f3e9a76e6d070f9a.s3.us-west-1.vpce.amazonaws.com \
  --push-log-dir=./logs \
  --object-prefix=$(hostname -f)/$(date --utc --iso-8601=s)
```

```buttonless title="Output"
Uploaded ./logs/stupefied-ptolemy.log to boto-demo-s3z/loghost.example.com/2024-07-11T18:13:47+00:00
Uploaded ./logs/modest-feynman.log to boto-demo-s3z/loghost.example.com/2024-07-11T18:13:47+00:00
Uploaded ./logs/priceless-einstein.log to boto-demo-s3z/loghost.example.com/2024-07-11T18:13:47+00:00
Uploaded ./logs/gallant-bardeen.log to boto-demo-s3z/loghost.example.com/2024-07-11T18:13:47+00:00
Uploaded ./logs/epic-heisenberg.log to boto-demo-s3z/loghost.example.com/2024-07-11T18:13:47+00:00
Uploaded ./logs/vibrant-galileo.log to boto-demo-s3z/loghost.example.com/2024-07-11T18:13:47+00:00
Uploaded ./logs/hopeful-wilson.log to boto-demo-s3z/loghost.example.com/2024-07-11T18:13:47+00:00
Uploaded ./logs/distracted-golick.log to boto-demo-s3z/loghost.example.com/2024-07-11T18:13:47+00:00
Uploaded ./logs/youthful-poitras.log to boto-demo-s3z/loghost.example.com/2024-07-11T18:13:47+00:00
Uploaded ./logs/agitated-curie.log to boto-demo-s3z/loghost.example.com/2024-07-11T18:13:47+00:00
```