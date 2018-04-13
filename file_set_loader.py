import os
import re
import hashlib
import boto
from curried import curried
from future import Future


class Item:

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

    return hash_func(read_bytes_func(file))


def read_bytes(file):

    with open(file, "rb") as file_data:

        return file_data.read()


def md5_hash(data_bytes):

    return hashlib.md5(data_bytes).hexdigest()


hash_file = hash_file_template(read_bytes)(md5_hash)


def trim_prefix(string, prefix): return re.sub(f"^{prefix}", '', string, count = 1)


def trim_path_prefix(string, prefix): return trim_prefix(trim_prefix(string, prefix), os.path.sep)

@curried
def enumerate_local_files_template(hash_file_func, list_files_func, local_path):

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


enumerate_local_files = enumerate_local_files_template(hash_file)(os.walk)


@curried
def enumerate_s3_files_template(get_bucket_func, get_prefixed_keys_from_bucket_func, s3_bucket, s3_path):

    return \
    (
        Item
        (
            "",
            trim_path_prefix(key.name, s3_path),
            key.etag.strip('"').strip("'")
        )
        for key in get_prefixed_keys_from_bucket_func(get_bucket_func(s3_bucket), s3_path)
        if not key.name.endswith('/')  # We don't care about "directories"
    )


def get_bucket(s3_bucket):

    return boto.connect_s3().get_bucket(s3_bucket)


def get_prefixed_keys_from_bucket(bucket, s3_path):

    return bucket.list(prefix = s3_path)


enumerate_s3_files = enumerate_s3_files_template(get_bucket)(get_prefixed_keys_from_bucket)


class FileSetLoader:

    @staticmethod
    def get_file_sets(local_path, s3_bucket, s3_path):

        local_future = Future(set, (enumerate_local_files(local_path),))
        s3_future = Future(set, (enumerate_s3_files(s3_bucket)(s3_path),))

        Future.wait_all(local_future, s3_future)

        if local_future.has_failed():

            print("enumerating local files failed!")
            print(f"Future.error => {local_future.error}")
            raise local_future.error

        if s3_future.has_failed():

            print("enumerating s3 files failed!")
            print(f"Future.error => {s3_future.error}")
            raise s3_future.error

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
    def test_get_prefixed_keys_from_bucket_returns_keys():
        from boto.s3.key import Key
        from boto.s3.bucket import Bucket

        expected_key_list = [Key(name = "blah1"), Key(name = "blah2"), Key(name = "blah3")]
        expected_prefix = "stacks"

        # define my own implementation of list
        def hijacked_list(prefix):
            assert prefix == expected_prefix
            return expected_key_list

        bucket = Bucket()
        bucket.list = hijacked_list  # override Bucket's list function with my implementation

        # should call my list instead of the original
        keys = get_prefixed_keys_from_bucket(bucket, expected_prefix)

        assert keys == expected_key_list

