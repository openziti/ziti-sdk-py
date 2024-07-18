#!/usr/bin/env python

import argparse
import os

from boto3 import client

import openziti


def configure_openziti(ziti_identity_file):
    print("Configuring with",
          f"identity file '{ziti_identity_file}'")
    return openziti.load(ziti_identity_file)


def push_logs_to_s3(bucket_name, bucket_endpoint,
                    push_log_dir, object_prefix):
    s3 = client(service_name='s3', endpoint_url=bucket_endpoint)

    for file_name in os.listdir(push_log_dir):
        if file_name.endswith(".log"):
            file_path = os.path.join(push_log_dir, file_name)
            with openziti.monkeypatch():
                if object_prefix:
                    s3.upload_file(file_path, bucket_name,
                                   f"{object_prefix}/{file_name}")
                    print(f"Uploaded {file_path} to",
                          f"{bucket_name}/{object_prefix}")
                else:
                    s3.upload_file(file_path, bucket_name, file_name)
                    print(f"Uploaded {file_path} to {bucket_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ziti-identity-file', required=True,
                        help='Ziti identity file')
    parser.add_argument('--bucket-name', required=True,
                        help='S3 bucket name')
    parser.add_argument('--bucket-endpoint', required=True,
                        help='S3 VPCEndpoint Interface URL')
    parser.add_argument('--object-prefix', required=False, default='',
                        help='Object key prefix in bucket')
    parser.add_argument('--push-log-dir', required=False, default='.',
                        help='Directory containing *.log files to upload')
    args = parser.parse_args()

    sts = client('sts')
    caller = sts.get_caller_identity()
    print("\nAuthenticated to AWS as:",
          f"UserId: {caller.get('UserId')}",
          f"Account: {caller.get('Account')}",
          f"Arn: {caller.get('Arn')}\n", sep="\n\t")

    configure_openziti(
        args.ziti_identity_file,
    )

    push_logs_to_s3(
        args.bucket_name,
        args.bucket_endpoint,
        args.push_log_dir,
        args.object_prefix
    )
