#!/usr/bin/env python

"""automation-stack-sync.py:
This script syncs the local directory to a given s3 bucket based on file size alone. Any
files missing locally but present on the S3 bucket will be removed from the s3 bucket.

The purpose of this script is to ensure that whatever was in a given git repo, is what is in the s3 bucket.
"""
from subprocess import run
import yaml

with open("automation-config.yaml", 'r') as ymlconfig:
    config = yaml.load(ymlconfig)

s3bucket = config['Bucket']

# SYNC TEMPLATES (raise exception on error)
run(["aws", "s3", "sync", "templates", "s3://" + s3bucket + "/templates", "--size-only", "--delete"], check=True)

# SYNC STACKS (raise exception on error)
run(["aws", "s3", "sync", "stacks", "s3://" + s3bucket + "/stacks", "--size-only", "--delete"], check=True)
