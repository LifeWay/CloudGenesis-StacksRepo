import threading


class Future(threading.Thread):

    def __repr__(self):

        return f'Future(func: {self.func}, args: {self.args}, completed: {self.completed}, succeeded: ' + \
               '{self.succeeded}, failed: {self.failed}, result: {self.result}, error: {self.error}'

    def __str__(self):

        return repr(self)

    def __init__(self, func, args = None):

        threading.Thread.__init__(self)
        self.func = func
        self.args = args
        self.completed = threading.Event()
        self.succeeded = threading.Event()
        self.failed = threading.Event()
        self.result = None
        self.error = None
        self.start()

    def run(self):

        try:

            if self.args is None:

                self.result = self.func()

            else:

                self.result = self.func(*self.args)

            self.succeeded.set()

        except Exception as error:

            self.error = error
            self.failed.set()

        self.completed.set()

    def wait(self):

        self.completed.wait()

    def has_completed(self):

        return self.completed.is_set()

    def has_succeeded(self):

        return self.succeeded.is_set()

    def has_failed(self):

        return self.failed.is_set()

    @staticmethod
    def wait_all(*futures):

        for future in futures:

            future.wait()