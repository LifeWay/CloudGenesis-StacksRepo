from file_set_loader import Item

class S3Diff:

    """Exposes the difference with semantics between two file sets"""

    @staticmethod
    def get_local_files_changed(local_file_set, s3_file_set):

        """Simple function that adds semantics to the set.difference call"""

        return local_file_set.difference(s3_file_set)

    @staticmethod
    def get_local_files_removed(local_file_set, s3_file_set):

        """Simple function that modifies the set of items to only consider file names (no e-Tags), diffs the two
        sets, and then filters the s3_file_set objects to include only files which need to be removed."""

        local_file_name_set = set(map(lambda i: i.file, local_file_set))
        s3_file_name_set = set(map(lambda i: i.file, s3_file_set))

        file_name_remove_set = s3_file_name_set.difference(local_file_name_set)

        return set(filter(lambda i: i.file in file_name_remove_set, s3_file_set))


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
        local_set = {Item("", "a.yaml", "hasha"), Item("", "b.yaml", "hashb"), Item("", "c.yaml", "hashc")}
        remote_set = {Item("", "a.yaml", "hasha"), Item("", "b.yaml", "hashb"), Item("", "c.yaml", "hashc")}
        assert S3Diff.get_local_files_removed(set(), set()) == set()
        assert S3Diff.get_local_files_removed(local_set, remote_set) == set()

    @staticmethod
    def test_get_local_files_removed_returns_empty_set_if_local_set_contains_all_of_remote_set():
        local_set = {Item("", "a.yaml", "hasha"), Item("", "b.yaml", "hashb"), Item("", "c.yaml", "hashc"), Item("", "d.yaml", "hashd"), Item("", "e.yaml", "hashe")}
        remote_set = {Item("", "a.yaml", "hasha"), Item("", "b.yaml", "hashb"), Item("", "c.yaml", "hashc")}
        assert S3Diff.get_local_files_removed(local_set, remote_set) == set()

    @staticmethod
    def test_get_local_files_removed_returns_items_in_local_set_that_do_not_equal_items_in_remote_set():
        local_set = {Item("", "a.yaml", "hasha"), Item("", "b.yaml", "hashb"), Item("", "c.yaml", "hashc")}
        remote_set = {Item("", "a.yaml", "hasha"), Item("", "b.yaml", "hashb"), Item("", "c.yaml", "hashc"), Item("", "d.yaml", "hashd"), Item("", "e.yaml", "hashe")}
        remove_set = {Item("","d.yaml", "hashd"), Item("", "e.yaml", "hashe")}

        print (S3Diff.get_local_files_removed(local_set, remote_set))
        assert S3Diff.get_local_files_removed(local_set, remote_set) == set(remove_set)
