#!/usr/bin/env python

"""automation-stack-sync.py:
This script syncs the local directory to a given s3 bucket based on file hash alone. Any
files missing locally but present on the S3 bucket will be removed from the s3 bucket.

The purpose of this script is to ensure that whatever was in a given git repo, is what is in the s3 bucket.
"""

import argparse
from s3_diff import S3Diff
from s3_updater import S3Updater
from file_set_loader import FileSetLoader


def sync_changes(local_path, s3_bucket, s3_path):

    """
    Determines which files have changed and been deleted locally and syncs those changes to S3

    :param local_path: The path to the local directory to compare with the files on S3
    :param s3_bucket: The bucket on S3 to use for comparision
    :param s3_path: The path to the s3 "directory" to compare with the local files
    :return: Nothing
    """

    (local_set, s3_set) = FileSetLoader.get_file_sets(local_path, s3_bucket, s3_path)

    files_to_update = S3Diff.get_local_files_changed(local_set, s3_set)
    files_to_remove = S3Diff.get_local_files_removed(local_set, s3_set)

    S3Updater.delete_files(map(lambda item: s3_path + "/" + item.file, files_to_remove), s3_bucket)
    S3Updater.upload_files(map(lambda item: item.file, files_to_update), local_path, s3_bucket, s3_path)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("local_path", help = "The path to the local directory to validate")
    parser.add_argument("s3_bucket", help = "The name of the s3 bucket to use to determine changed files")
    parser.add_argument("s3_path", help = "The path into the s3 bucket corresponding to local_path")
    args = parser.parse_args()

    sync_changes(args.local_path, args.s3_bucket, args.s3_path)