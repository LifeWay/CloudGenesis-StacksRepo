#!/usr/bin/env python

"""automation-linter-files-filter.py:
This script compares what is in the S3 bucket to what came over from the git repo. We take capture the files that are
being changed so that they can be linted and tested prior to launch without re-testing / re-linting the entire repo.
"""
import os
import argparse
from boto.exception import BotoServerError
from boto.cloudformation import connect_to_region
from boto.cloudformation.connection import CloudFormationConnection


def get_changed_files(local_path, s3_bucket, s3_path):

    from s3_diff import S3Diff
    from file_set_loader import FileSetLoader

    (local_set, s3_set) = FileSetLoader.get_file_sets(local_path, s3_bucket, s3_path)

    return S3Diff.get_local_files_changed(local_set, s3_set)


def validate_templates(file_list):

    valid = True
    conn = connect_to_region(CloudFormationConnection.DefaultRegionName)

    for file in file_list:
        with open(file, "r") as file_data:
            try:
                conn.validate_template(template_body = file_data.read())
                print(f"{file} => Valid")
            except BotoServerError as error:
                print(f"{file} => {error.message}")
                valid = False

    return valid


def validate_changed_templates(local_path, s3_bucket, s3_path):

    changed_files = get_changed_files(local_path, s3_bucket, s3_path)

    return validate_templates  \
    (
        map
        (
            lambda item: os.path.join(local_path, item.file),
            changed_files
        )
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("local_path", help = "The path to the local directory to validate")
    parser.add_argument("s3_bucket", help = "The name of the s3 bucket to use to determine changed files")
    parser.add_argument("s3_path", help = "The path into the s3 bucket corresponding to local_path")
    args = parser.parse_args()

    if validate_changed_templates(args.local_path, args.s3_bucket, args.s3_path):
        exit(0)
    else:
        exit(1)