import os
import boto3
from curried import curried
from common import Struct


def prepend_path(path, file):

    """
    Prepends a path string to a file name

    :param path: The path to prepend
    :param file: The file name to which to prepend
    :return: The path + file name string
    """

    return os.path.join(path, file)


def get_s3_client():

    """Returns an S3 client that can create Bucket objects"""

    return boto3.resource("s3")


def get_bucket(s3, s3_bucket):

    """
    Returns an object representing an S3 bucket

    :param s3: An S3 client
    :param s3_bucket: The name of the S3 bucket
    :return: An object representing an S3 bucket
    """

    return s3.Bucket(s3_bucket)


@curried
def delete_files_template(get_s3_client_func, get_bucket_func, delete_keys_func, key_list, s3_bucket):

    """
    Curried template function for deleting files from an S3 bucket

    :param get_s3_client_func: A function that returns an S3 client
    :param get_bucket_func: A function that returns an object representing an S3 bucket
    :param delete_keys_func: A function that deletes a list of keys from an S3 bucket
    :param key_list: The list of keys to delete from the S3 bucket
    :param s3_bucket: The name of the bucket from which to delete
    :return: A MultiDeleteResult object detailing the keys that were deleted and any errors encountered
    """

    return delete_keys_func \
    (
        get_bucket_func
        (
            get_s3_client_func(),
            s3_bucket
        ),
        key_list
    )


def delete_keys(s3_bucket, key_list):

    """
    Deletes the specified list of keys from the specified bucket

    :param s3_bucket: The bucket from which to delete
    :param key_list: The list of keys to delete from the S3 bucket
    :return: A MultiDeleteResult object detailing the keys that were deleted and any errors encountered
    """

    delete = \
    {
        "Objects" :
        [
            { "Key": key }
            for key in key_list
        ]
    }

    if len(delete["Objects"]) > 0:

        response = s3_bucket.delete_objects(Delete = delete)

        return Struct(deleted = response.get("Deleted", []), errors = response.get("Errors", []))

    else:

        return Struct(deleted=[], errors=[])


# Curry the get_bucket (from file_set_loader) and delete_keys functions into the delete_files_template function
delete_files = delete_files_template(get_s3_client)(get_bucket)(delete_keys)


@curried
def upload_files_template \
(
    get_s3_client_func,
    get_bucket_func,
    upload_file_func,
    local_file_set,
    local_path,
    s3_bucket,
    s3_path
):

    """
    Curried template function for uploading files to an S3 bucket

    :param get_s3_client_func: A function that returns an S3 client
    :param get_bucket_func: A function that returns an object representing an S3 bucket
    :param upload_file_func: A function that uploads a file to a specified key in an S3 bucket
    :param local_file_set: The set of local files to upload
    :param local_path: The path to the local files to upload
    :param s3_bucket: The S3 bucket to which to upload
    :param s3_path: The path into the S3 bucket to which to upload
    :return: Nothing
    """

    s3 = get_s3_client_func()
    bucket = get_bucket_func(s3, s3_bucket)

    for file in local_file_set:

        upload_file_func    \
        (
            bucket,
            prepend_path(local_path, file),
            prepend_path(s3_path, file)
        )


def upload_file(bucket, key_path, file):

    """
    Creates a key object representing a key in the specified bucket

    :param bucket: The bucket in which the key resides
    :param key_path: The path into the bucket in which the key resides
    :param file: The file to upload to the key object
    :return: The key object
    """

    return bucket.upload_file(file, key_path)




# Curry the get_s3_client, get_bucket, and upload_file functions into the upload_files_template function
upload_files = upload_files_template(get_s3_client)(get_bucket)(upload_file)


class S3Updater:

    """Wrapper class that makes calling upload_files and delete_files a little nicer"""

    @staticmethod
    def upload_files(local_file_set, local_path, s3_bucket, s3_path):

        """
        Upload files to an S3 bucket

        :param local_file_set: The set of local files to upload
        :param local_path: The path to the local files to upload
        :param s3_bucket: The S3 bucket to which to upload
        :param s3_path: The path into the S3 bucket to which to upload
        :return: Nothing
        """

        return upload_files(local_file_set)(local_path)(s3_bucket)(s3_path)

    @staticmethod
    def delete_files(key_list, s3_bucket):

        """
        Delete files from an S3 bucket

        :param key_list: The list of keys to delete from the S3 bucket
        :param s3_bucket: The name of the bucket from which to delete
        :return: A MultiDeleteResult object detailing the keys that were deleted and any errors encountered
        """

        return delete_files(key_list)(s3_bucket)


class PyTests:

    @staticmethod
    def test_prepend_path_should_prepend_the_specified_path_to_the_file_name_separated_by_dir_separator():

        assert prepend_path("path/to", "myfile.txt") == "path/to/myfile.txt"


    @staticmethod
    def test_get_bucket_should_ask_the_s3_client_to_get_a_bucket():

        expected_bucket_name = "my_bucket"

        s3 = get_s3_client()

        expected_bucket = s3.Bucket(expected_bucket_name)

        def hijacked_bucket(s3_bucket):
            assert s3_bucket == expected_bucket_name
            return expected_bucket

        s3.Bucket = hijacked_bucket

        assert get_bucket(s3, expected_bucket_name) == expected_bucket


    @staticmethod
    def test_delete_files_template_should_call_get_bucket_func_with_correct_parameter():

        get_bucket_called = False
        bucket_name = "my_bucket"

        def get_bucket(s3, s3_bucket):
            nonlocal get_bucket_called
            get_bucket_called = True
            assert s3_bucket == bucket_name

        delete_files_template           \
            (get_s3_client)             \
            (get_bucket)                \
            (lambda bucket, keys: True) \
            (())                        \
            (bucket_name)

        assert get_bucket_called

    @staticmethod
    def test_delete_files_template_should_call_delete_keys_func_with_correct_parameters():

        delete_keys_called = False
        expected_bucket = "my_bucket"
        s3 = get_s3_client()
        bucket = s3.Bucket(expected_bucket)
        keys = ("key1", "key2", "key3")

        def delete_keys(s3_bucket, key_list):
            nonlocal delete_keys_called
            delete_keys_called = True
            assert s3_bucket == bucket
            assert key_list == keys

        delete_files_template               \
            (lambda: s3)                    \
            (lambda s3, s3_bucket: bucket)  \
            (delete_keys)                   \
            (keys)                          \
            (expected_bucket)

        assert delete_keys_called

    @staticmethod
    def test_delete_keys_should_append_errors_to_error_list():

        key_list = ["key1", "key2", "key3", "key4", "key5"]
        good_keys = ["key1", "key2", "key4", "key5"]

        def hijacked_delete_objects(Delete):

            response = {"Deleted":[], "Errors":[]}

            for obj in Delete["Objects"]:
                key = obj["Key"]
                if key not in good_keys:
                    response["Errors"].append(key)
                else:
                    response["Deleted"].append(key)

            return response

        bucket = get_bucket(get_s3_client(), "my_bucket")
        bucket.delete_objects = hijacked_delete_objects

        res = delete_keys(bucket, key_list)

        assert res.deleted == good_keys
        assert len(res.errors) == 1
        assert res.errors[0] == "key3"

    @staticmethod
    def test_upload_files_template_should_call_get_bucket_func_with_correct_parameter():

        get_bucket_called = False
        bucket_name = "my_bucket"

        expected_s3 = get_s3_client()

        def get_bucket(s3, s3_bucket):
            nonlocal get_bucket_called
            get_bucket_called = True
            assert s3 == expected_s3
            assert s3_bucket == bucket_name

        upload_files_template                   \
            (lambda: expected_s3)               \
            (get_bucket)                        \
            (lambda bucket, key, file: True)    \
            ({})                                \
            ("")                                \
            (bucket_name)                       \
            ("")

        assert get_bucket_called

    @staticmethod
    def test_upload_files_template_should_call_upload_file_func_for_each_file_in_local_file_set():

        s3_path = "foo"
        bucket = "my_bucket"
        local_path = "my/files/path"
        local_file_set = {"file1", "file2", "file3"}

        expected_parameters = \
        [
            (f"{s3_path}/{file}", f"{os.path.join(local_path, file)}")
            for file in local_file_set
        ]

        actual_parameters = []

        def my_upload_file(s3_bucket, local_file, s3_path):
            assert s3_bucket == bucket
            actual_parameters.append((s3_path, local_file))

        upload_files_template               \
            (get_s3_client)                 \
            (lambda s3, s3_bucket: bucket)  \
            (my_upload_file)                \
            (local_file_set)                \
            (local_path)                    \
            (bucket)                        \
            (s3_path)

        assert actual_parameters == expected_parameters








