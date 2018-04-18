import threading


class Future(threading.Thread):

    """
    Encapsulates running a function in an asynchronous manner
    """

    def __repr__(self):

        return f'Future(func: {self.func}, args: {self.args}, completed: {self.completed}, succeeded: ' + \
               '{self.succeeded}, failed: {self.failed}, result: {self.result}, error: {self.error}'

    def __str__(self):

        return repr(self)

    def __init__(self, func, args = None):

        """Build and start the Future"""

        # Define items that the underlying Thread class needs
        threading.Thread.__init__(self)
        self.func = func
        self.args = args

        # Define items needed for reporting success/failure/completion
        self.completed = threading.Event()
        self.succeeded = threading.Event()
        self.failed = threading.Event()

        # Define items needed for returning the result or error
        self.result = None
        self.error = None

        # Start the underlying Thread object
        self.start()

    def run(self):

        """
        The code to execute asynchronously
        :return:
        """

        try:

            # Call the specified function and store the result
            if self.args is None:

                self.result = self.func()

            else:

                self.result = self.func(*self.args)

            # Signal success
            self.succeeded.set()

        except Exception as error:

            # On exception, store the error and signal failure
            self.error = error
            self.failed.set()

        # In either event, signal completion
        self.completed.set()

    def wait(self):

        """Wait for completion"""

        self.completed.wait()

    def has_completed(self):

        """Determine if the Future has completed"""

        return self.completed.is_set()

    def has_succeeded(self):

        """Determine if the Future has succeeded"""

        return self.succeeded.is_set()

    def has_failed(self):

        """Determine if the Future has failed"""

        return self.failed.is_set()

    @staticmethod
    def wait_all(*futures):

        """
        Waits for all futures in a list to complete before returning

        :param futures: The list of futures awaiting completion
        :return: Nothing
        """

        for future in futures:

            future.wait()