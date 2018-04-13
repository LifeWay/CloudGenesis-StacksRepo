class S3Diff:

    @staticmethod
    def get_local_files_changed(local_file_set, s3_file_set):

        return local_file_set.difference(s3_file_set)

    @staticmethod
    def get_local_files_removed(local_file_set, s3_file_set):

        return s3_file_set.difference(local_file_set)


class PyTests:

    @staticmethod
    def test_get_local_files_changed_returns_empty_set_if_both_input_sets_are_equal():
        assert S3Diff.get_local_files_changed(set(), set()) == set()
        assert S3Diff.get_local_files_changed({1, 2, 3}, {1, 2, 3}) == set()

    @staticmethod
    def test_get_local_files_changed_returns_empty_set_if_remote_set_contains_all_of_local_set():
        assert S3Diff.get_local_files_changed({1, 2, 3}, {1, 2, 3, 4, 5}) == set()

    @staticmethod
    def test_get_local_files_changed_returns_items_in_local_set_that_do_not_equal_items_in_remote_set():
        assert S3Diff.get_local_files_changed({1, 3, 5, 7, 9}, {1, 2, 3, 4, 5}) == {7, 9}

    @staticmethod
    def test_get_local_files_removed_returns_empty_set_if_both_input_sets_are_equal():
        assert S3Diff.get_local_files_removed(set(), set()) == set()
        assert S3Diff.get_local_files_removed({1, 2, 3}, {1, 2, 3}) == set()

    @staticmethod
    def test_get_local_files_removed_returns_empty_set_if_local_set_contains_all_of_remote_set():
        assert S3Diff.get_local_files_removed({1, 2, 3, 4, 5}, {1, 2, 3}) == set()

    @staticmethod
    def test_get_local_files_removed_returns_items_in_local_set_that_do_not_equal_items_in_remote_set():
        assert S3Diff.get_local_files_removed({1, 2, 3, 4, 5}, {1, 3, 5, 7, 9}) == {7, 9}
