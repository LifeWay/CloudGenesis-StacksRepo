import os
import boto
from curried import curried
from file_set_loader import get_bucket
from boto.s3.multidelete import MultiDeleteResult


def prepend_path(path, file):

    return os.path.join(path, file)


@curried
def delete_files_template(get_bucket_func, delete_keys_func, key_list, s3_bucket):

    return delete_keys_func(get_bucket_func(s3_bucket), key_list)


def delete_keys(s3_bucket, key_list):

    result = MultiDeleteResult(s3_bucket)

    for key in key_list:

        try:

            result.deleted.append(s3_bucket.delete_key(key))

        except Exception as error:

            result.errors.append(error)

    return result


delete_files = delete_files_template(get_bucket)(delete_keys)


@curried
def upload_files_template \
(
    get_bucket_func,
    create_key_func,
    set_key_contents_func,
    local_file_set,
    local_path,
    s3_bucket,
    s3_path
):

    bucket = get_bucket_func(s3_bucket)

    for file in local_file_set:

        set_key_contents_func \
        (
            create_key_func
            (
                bucket,
                prepend_path(s3_path, file)
            ),
            prepend_path(local_path, file)
        )


def create_s3_key(bucket, key_path):

    return bucket.new_key(key_path)


def set_s3_key_contents(key, file):

    return key.set_contents_from_filename(file)


upload_files = upload_files_template(get_bucket)(create_s3_key)(set_s3_key_contents)


class S3Updater:

    @staticmethod
    def upload_files(local_file_set, local_path, s3_bucket, s3_path):

        return upload_files(local_file_set)(local_path)(s3_bucket)(s3_path)

    @staticmethod
    def delete_files(key_list, s3_bucket):

        return delete_files(key_list)(s3_bucket)


class PyTests:

    @staticmethod
    def test_prepend_path_should_prepend_the_specified_path_to_the_file_name_separated_by_dir_separator():

        assert prepend_path("path/to", "myfile.txt") == "path/to/myfile.txt"

    @staticmethod
    def test_delete_files_template_should_call_get_bucket_func_with_correct_parameter():

        get_bucket_called = False
        bucket_name = "my_bucket"

        def get_bucket(s3_bucket):
            nonlocal get_bucket_called
            get_bucket_called = True
            assert s3_bucket == bucket_name

        delete_files_template           \
            (get_bucket)                \
            (lambda bucket, keys: True) \
            (())                        \
            (bucket_name)

        assert get_bucket_called

    @staticmethod
    def test_delete_files_template_should_call_delete_keys_func_with_correct_parameters():

        delete_keys_called = False
        bucket = boto.s3.bucket.Bucket()
        keys = ("key1", "key2", "key3")

        def delete_keys(s3_bucket, key_list):
            nonlocal delete_keys_called
            delete_keys_called = True
            assert s3_bucket == bucket
            assert key_list == keys

        delete_files_template           \
            (lambda s3_bucket: bucket)  \
            (delete_keys)               \
            (keys)                      \
            ("my_bucket")

        assert delete_keys_called

    @staticmethod
    def test_delete_keys_should_call_Bucket_delete_key_for_each_key_passed_to_it():

        deleted_keys = []
        key_list = ["key1", "key2", "key3", "key4", "key5"]

        def hijacked_delete_key(key):
            deleted_keys.append(key)

        bucket = boto.s3.bucket.Bucket()
        bucket.delete_key = hijacked_delete_key

        delete_keys(bucket, key_list)

        assert key_list == deleted_keys

    @staticmethod
    def test_delete_keys_should_append_errors_to_error_list():

        key_list = ["key1", "key2", "key3", "key4", "key5"]
        good_keys = ["key1", "key2", "key4", "key5"]

        def hijacked_delete_key(key):
            if key not in good_keys:
                raise KeyError(key)
            else:
                return key

        bucket = boto.s3.bucket.Bucket()
        bucket.delete_key = hijacked_delete_key

        res = delete_keys(bucket, key_list)

        assert res.deleted == good_keys
        assert len(res.errors) == 1
        assert isinstance(res.errors[0], KeyError)

    @staticmethod
    def test_upload_files_template_should_call_get_bucket_func_with_correct_parameter():

        get_bucket_called = False
        bucket_name = "my_bucket"

        def get_bucket(s3_bucket):
            nonlocal get_bucket_called
            get_bucket_called = True
            assert s3_bucket == bucket_name

        upload_files_template           \
            (get_bucket)                \
            (lambda bucket, key: True)  \
            (lambda key, file: True)    \
            ({})                        \
            ("")                        \
            (bucket_name)               \
            ("")

        assert get_bucket_called

    @staticmethod
    def test_upload_files_template_should_call_set_key_content_func_for_each_file_in_local_file_set():

        s3_path = "foo"
        bucket = "my_bucket"
        local_path = "my/files/path"
        local_file_set = {"file1", "file2", "file3"}

        expected_parameters = \
        [
            (f"s3://{bucket}/{s3_path}/{file}", f"{os.path.join(local_path, file)}")
            for file in local_file_set
        ]

        actual_parameters = []

        def my_set_key_contents(s3_path, local_file):
            actual_parameters.append((s3_path, local_file))

        upload_files_template                                   \
            (lambda s3_bucket: bucket)                          \
            (lambda s3_bucket, file: f"s3://{bucket}/{file}")   \
            (my_set_key_contents)                               \
            (local_file_set)                                    \
            (local_path)                                        \
            (bucket)                                            \
            (s3_path)

        assert actual_parameters == expected_parameters

    @staticmethod
    def test_upload_files_template_should_call_create_key_func_for_each_file_in_local_file_set():

        s3_path = "foo"
        bucket = "my_bucket"
        local_path = "my/files/path"
        local_file_set = {"file1", "file2", "file3"}

        expected_parameters = \
        [
            f"s3://{bucket}/{s3_path}/{file}"
            for file in local_file_set
        ]

        actual_parameters = []

        def my_create_key(bucket, s3_file):
            val = f"s3://{bucket}/{s3_file}"
            actual_parameters.append(val)
            return val

        upload_files_template               \
            (lambda s3_bucket: bucket)      \
            (my_create_key)                 \
            (lambda s3_bucket, key: True)   \
            (local_file_set)                \
            (local_path)                    \
            (bucket)                        \
            (s3_path)

        assert actual_parameters == expected_parameters

    @staticmethod
    def test_create_s3_key_should_call_new_key_on_bucket():

        new_key_called = False
        expected_key_path = "path/to/my/key"

        def hijacked_new_key(key_path):
            nonlocal new_key_called
            new_key_called = True
            assert key_path == expected_key_path

        bucket = boto.s3.bucket.Bucket()
        bucket.new_key = hijacked_new_key

        create_s3_key(bucket, expected_key_path)

        assert new_key_called

    @staticmethod
    def test_set_s3_key_contents_should_call_set_contents_from_filename_on_key():

        set_contents_called = False
        expected_file = "path/to/my/file"

        def hijacked_set_contents_from_filename(file):
            nonlocal set_contents_called
            set_contents_called = True
            assert file == expected_file

        key = boto.s3.key.Key()
        key.set_contents_from_filename = hijacked_set_contents_from_filename

        set_s3_key_contents(key, expected_file)

        assert set_contents_called


