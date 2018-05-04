#!/usr/bin/env python

"""automation-linter-files-filter.py:
This script compares what is in the S3 bucket to what came over from the git repo. We take capture the files that are
being changed so that they can be linted and tested prior to launch without re-testing / re-linting the entire repo.
"""
import os
import boto3
import shutil
import argparse
from botocore.exceptions import ClientError


def get_changed_files(local_path, s3_bucket, s3_path):

    """
    Gets the list of local files that have changed in relation to the specified path into the S3 bucket

    @:param local_path: The path to the local directory to compare with the files on S3
    @:param s3_bucket: The bucket on S3 to use for comparision
    @:param s3_path: The path to the s3 "directory" to compare with the local files

    @:return: The list of changed files
    """

    from s3_diff import S3Diff
    from file_set_loader import FileSetLoader

    (local_set, s3_set) = FileSetLoader.get_file_sets(local_path, s3_bucket, s3_path)

    return S3Diff.get_local_files_changed(local_set, s3_set)


def copy_files_to_dir(source_dir, dest_dir, file_list):

    """
    Copies file from one directory to another.

    :param source_dir: The source directory
    :param dest_dir: The destination directory
    :param file_list: List of Item objects representing the files
    :return:
    """

    # Make sure the dest directory at least exists, so cfn_nag won't blow up
    os.makedirs(dest_dir, exist_ok = True)

    for file in file_list:

        source_file = os.path.join(source_dir, file.file)
        dest_file = os.path.join(dest_dir, file.file)

        os.makedirs(os.path.dirname(dest_file), exist_ok = True)

        shutil.copy(source_file, dest_file)


def validate_templates(file_list):

    """
    Validates the files in file_list as AWS CloudFormation templates

    :param file_list: The list of files to validate
    :return: Whether all files are valid templates or not
    """

    valid = True

    client = boto3.client("cloudformation")

    for file in file_list:

        with open(file, "r") as file_data:

            try:

                client.validate_template(TemplateBody = file_data.read())
                print(f"{file} => Valid")

            except ClientError as error:

                print(f"{file} => {error}")
                valid = False

    return valid


def validate_changed_templates(local_path, s3_bucket, s3_path):

    """
    Gets the list of changed local files in relation to a path into an S3 bucket and validates them as CloudFormation templates.

    :param local_path: The path to the local directory to compare with the files on S3
    :param s3_bucket: The bucket on S3 to use for comparision
    :param s3_path: The path to the s3 "directory" to compare with the local files
    :return: Whether all files are valid templates or not
    """

    changed_files = get_changed_files(local_path, s3_bucket, s3_path)

    valid = validate_templates  \
    (
        map
        (
            lambda item: os.path.join(local_path, item.file),
            changed_files
        )
    )

    if valid:

        try:

            copy_files_to_dir(local_path, local_path + "-changed", changed_files)

        except Exception as error:

            print(f"Copying files to temp directory failed => {error}")
            valid = False

    return valid


if __name__ == "__main__":

    """Parses command-line parameters and returns 0 if all changed files are valid else 1"""

    parser = argparse.ArgumentParser()
    parser.add_argument("local_path", help = "The path to the local directory to validate")
    parser.add_argument("s3_bucket", help = "The name of the s3 bucket to use to determine changed files")
    parser.add_argument("s3_path", help = "The path into the s3 bucket corresponding to local_path")
    args = parser.parse_args()

    if validate_changed_templates(args.local_path, args.s3_bucket, args.s3_path):
        exit(0)
    else:
        exit(1)