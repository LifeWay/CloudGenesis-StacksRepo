import os
import re
import hashlib
import boto3
from curried import curried
from future import Future
from common import Struct


class Item:

    """
    A class that combines file paths, names, and hashes in a comparable way
    """

    def __init__(self, file_path, file_name, file_hash = None):

        self.file = file_name if file_path == "" else os.path.join(file_path, file_name)
        self.file_hash = file_hash

    def __eq__(self, other):

        """Overrides the default implementation"""

        if isinstance(self, other.__class__):
            return self.file == other.file and self.file_hash == other.file_hash
        return NotImplemented

    def __hash__(self):

        """Overrides the default implementation"""

        return hash((self.file, self.file_hash))

    def __repr__(self):

        return f'Item(file: "{self.file}", file_hash: "{self.file_hash}")'

    def __str__(self):

        return repr(self)


@curried
def hash_file_template(read_bytes_func, hash_func, file):

    """
    Curried template function for hashing a file

    :param read_bytes_func: The function to use to read the bytes from the specified file
    :param hash_func: The hashing algorithm to use to hash the bytes from the file
    :param file: The file to hash
    :return: The hash value of the file
    """

    return hash_func(read_bytes_func(file))


def read_bytes(file):

    """
    Read the bytes as binary from the file

    :param file: The file from which to read
    :return: The binary data from the file
    """

    with open(file, "rb") as file_data:

        return file_data.read()


def md5_hash(data_bytes):

    """
    Hash the specified byte array with the MD5 algorithm

    :param data_bytes: The byte array to hash
    :return: The hash of the byte array
    """

    return hashlib.md5(data_bytes).hexdigest()


# Curry the read_bytes and md5_hash implementations into the hash_file_template function
hash_file = hash_file_template(read_bytes)(md5_hash)


def trim_prefix(string, prefix):

    """
    Trims a prefix from the start of a string

    :param string: The string to trim
    :param prefix: The prefix string to trim from the start of the string
    :return: The trimmed string
    """

    return re.sub(f"^{prefix}", '', string, count = 1)


def trim_path_prefix(string, prefix):

    """
    Trims a path prefix (including the path separator) from a string

    :param string: The string to trim
    :param prefix: The prefix string to trim from the start of the string
    :return: The trimmed string
    """

    return trim_prefix(trim_prefix(string, prefix), os.path.sep)


@curried
def enumerate_local_files_template(hash_file_func, list_files_func, local_path):

    """
    Curried template function for enumerating files and their hashes from a local directory

    :param hash_file_func: A function for computing the hash of a specified file
    :param list_files_func: A function that lists the files from a local directory
    :param local_path: The local directory to enumerate
    :return: A generator object that will provide the enumerated files
    """

    return \
    (
        Item
        (
            trim_path_prefix(root, local_path),
            file_name,
            hash_file_func(os.path.join(root, file_name))
        )
        for root, dir_names, file_names in list_files_func(local_path)
        for file_name in file_names
    )


# Curry the hash_file and os.walk functions into the enumerate_local_files_template function
enumerate_local_files = enumerate_local_files_template(hash_file)(os.walk)


@curried
def enumerate_s3_files_template(get_s3_client_func, get_prefixed_keys_from_bucket_func, s3_bucket, s3_path):

    """
    Curried template function for enumerating files and their hashes from a path into an S3 bucket

    :param get_s3_client_func: A function that returns an S3 client
    :param get_prefixed_keys_from_bucket_func: A function that gets a list of S3 keys with the specified prefix
    :param s3_bucket: The name of the S3 bucket to query
    :param s3_path: The path into the S3 bucket to query
    :return: A generator object that will provide the enumerated files
    """

    return \
    (
        Item
        (
            "",
            trim_path_prefix(key.name, s3_path),
            key.etag.strip('"').strip("'")
        )
        for key in get_prefixed_keys_from_bucket_func(get_s3_client_func(), s3_bucket, s3_path)
        if not key.name.endswith('/')  # We don't care about "directories"
    )


def get_s3_client():

    """Returns an s3 client for use by other functions"""

    return boto3.client('s3')


def get_prefixed_keys_from_bucket(s3, bucket, s3_path):

    """
        Gets a list of keys from the S3 bucket in the specified path

        :param s3: An S3 client
        :param bucket: The S3 bucket to query
        :param s3_path: The path into the S3 bucket to query
        :return: A generator that lists keys from the S3 bucket in the specified path
    """

    kwargs = { "Bucket": bucket, "Prefix": s3_path }

    while True:

        response = s3.list_objects_v2(**kwargs)

        for key in response["Contents"]:

            yield Struct(name = key["Key"], etag = key["ETag"])

        try:

            kwargs["ContinuationToken"] = response["NextContinuationToken"]

        except KeyError:

            break


# Curry the get_s3_client and get_prefixed_keys_from_bucket functions into the enumerate_s3_files_template function
enumerate_s3_files = enumerate_s3_files_template(get_s3_client)(get_prefixed_keys_from_bucket)


class FileSetLoader:

    """
    A class with a static method that allows files and hashes be enumerated from a local directory and an S3 location simultaneously
    """

    @staticmethod
    def get_file_sets(local_path, s3_bucket, s3_path):

        """
        Enumerates files and hashes from a local path and an S3 location simultaneously

        :param local_path: The local directory from which to enumerate its files and calculate their hashes
        :param s3_bucket: The S3 bucket to query
        :param s3_path: The path into the S3 bucket from which to enumerate its files and their hashes
        :return: Sets containing the local files and S3 files, respectively
        """

        # Calls set(enumerate_local_files(local_path)) asynchronously
        local_future = Future(set, (enumerate_local_files(local_path),))

        # Calls set(enumerate_s3_files(s3_bucket)(s3_path)) asynchronously
        s3_future = Future(set, (enumerate_s3_files(s3_bucket)(s3_path),))

        # Waits for both sets to be created
        Future.wait_all(local_future, s3_future)

        # Checks for failure in building the local set
        if local_future.has_failed():

            print("enumerating local files failed!")
            print(f"Future.error => {local_future.error}")
            raise local_future.error

        # Checks for failure in building the s3 set
        if s3_future.has_failed():

            print("enumerating s3 files failed!")
            print(f"Future.error => {s3_future.error}")
            raise s3_future.error

        # Return both sets on success
        return local_future.result, s3_future.result


class PyTests:

    @staticmethod
    def test_Item_constructor_handles_file_path_correctly():

        assert Item("foo", "bar").file == os.path.join("foo", "bar")
        assert Item("", "foobar").file == "foobar"

    @staticmethod
    def test_Item_constructor_handles_file_hash_correctly():

        assert Item("foo", "bar", None).file_hash is None
        assert Item("foo", "bar", "my_hash").file_hash == "my_hash"
        assert Item("", "foobar", None).file_hash is None
        assert Item("", "foobar", "my_hash").file_hash == "my_hash"

    @staticmethod
    def test_Item_eq_determines_two_equal_files_equal():

        item1 = Item("foo", "bar", "hash")
        item2 = Item("foo", "bar", "hash")

        assert item1 == item2

    @staticmethod
    def test_Item_eq_determines_two_unequal_files_unqual():

        item1 = Item("foo", "bar", "baz")
        item2 = Item("foo", "bar", None)
        item3 = Item("foo", "bar", "hash")
        item4 = Item("bar", "foo", "baz")
        item5 = Item("bar", "foo", None)
        item6 = Item("bar", "foo", "hash")

        assert item1 != item2
        assert item1 != item3
        assert item1 != item4
        assert item1 != item5
        assert item1 != item6

        assert item2 != item3
        assert item2 != item4
        assert item2 != item5
        assert item2 != item6

        assert item3 != item4
        assert item3 != item5
        assert item3 != item6

        assert item4 != item5
        assert item4 != item6

        assert item5 != item6

    @staticmethod
    def test_hash_file_template_should_pass_output_from_read_bytes_into_hash_function():

        expected_file = "my_file"
        expected_file_data_bytes = b"This is my file data"

        def my_read_bytes(file):

            assert file == expected_file
            return expected_file_data_bytes

        def my_hash(binary_data):

            assert binary_data == expected_file_data_bytes
            return hash(expected_file_data_bytes)

        assert hash_file_template(my_read_bytes)(my_hash)(expected_file) == hash(expected_file_data_bytes)

    @staticmethod
    def test_trim_prefix_should_trim_prefix():
        assert trim_prefix("bobobobobobbob", "bob") == "obobobobbob"
        assert trim_prefix("bobbobobobobob", "bob") == "bobobobobob"
        assert trim_prefix("ooobobbobobobo", "bob") == "ooobobbobobobo"

    @staticmethod
    def test_trim_path_prefix_should_trim_path_prefix():
        assert trim_path_prefix("this/is/my/path/prefix", "this") == "is/my/path/prefix"
        assert trim_path_prefix("this/is/my/path/prefix", "this/is") == "my/path/prefix"
        assert trim_path_prefix("this/is/my/path/prefix", "this/is/my") == "path/prefix"
        assert trim_path_prefix("this/is/my/path/prefix", "this/is/my/path") == "prefix"

    @staticmethod
    def test_enumerate_local_files_template():
        expected_path = "my_path"
        expected_file_names = ["file1.txt", "file2.txt"]
        expected_result = \
        [
            Item(file_path = "", file_name = "file1.txt", file_hash = "txt.1elif/htap_ym"),
            Item(file_path = "", file_name = "file2.txt", file_hash = "txt.2elif/htap_ym")
        ]

        def my_list_files(path):
            yield (path, "", expected_file_names)

        def my_hash_file(file):
            return file[::-1]

        res = enumerate_local_files_template(my_hash_file)(my_list_files)(expected_path)

        assert list(res) == expected_result

    @staticmethod
    def test_enumerate_s3_files_template():
        expected_path = "my_path"
        expected_key_names = ["file1.txt", "file2.txt"]
        expected_bucket_name = "my_bucket"
        expected_result = \
        [
            Item(file_path = "", file_name = "file1.txt", file_hash = "txt.1elif"),
            Item(file_path = "", file_name = "file2.txt", file_hash = "txt.2elif")
        ]

        def my_new_key(key_name, etag):
            return Struct(name = key_name, etag = etag)

        def my_get_prefixed_keys_from_bucket(s3, s3_bucket, s3_path):
            assert s3_bucket == expected_bucket_name
            assert s3_path == expected_path
            key_names = expected_key_names + ["dir1/"]

            return \
            [
                my_new_key(key_name, key_name[::-1])
                for key_name in key_names
            ]

        res = enumerate_s3_files_template       \
            (get_s3_client)                     \
            (my_get_prefixed_keys_from_bucket)  \
            (expected_bucket_name)              \
            (expected_path)

        assert list(res) == expected_result


    @staticmethod
    def test_get_prefixed_keys_from_bucket_returns_keys():

        expected_bucket = "bucket"
        expected_prefix = "stacks"
        expected_key_list = \
        [
            Struct(name = "blah1", etag = "1halb"),
            Struct(name = "blah2", etag = "2halb"),
            Struct(name = "blah3", etag = "3halb")
        ]

        # define my own implementation of list
        def hijacked_list(**kwargs):
            assert kwargs["Bucket"] == expected_bucket
            assert kwargs["Prefix"] == expected_prefix
            return \
            {
                "Contents": [{ "Key": key.name, "ETag": key.etag } for key in expected_key_list]
            }

        s3 = get_s3_client()
        s3.list_objects_v2 = hijacked_list  # override Bucket's list function with my implementation

        # should call my list instead of the original
        keys = list(get_prefixed_keys_from_bucket(s3, expected_bucket, expected_prefix))

        assert keys == expected_key_list

