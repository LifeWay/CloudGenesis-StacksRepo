from functools import partial
from inspect import signature


def curried(func):

    def inner(arg):

        if len(signature(func).parameters) == 1:

            return func(arg)

        else:

            return curried(partial(func, arg))

    return inner


class PyTests:

    @staticmethod
    def test_curried_returns_a_function_that_calls_a_function_with_a_single_argument():

        called = False

        def func1(blah):

            nonlocal called
            called = True
            return called

        func = curried(func1)

        assert len(signature(func).parameters) == 1
        assert func(0) == True
        assert called == True

    @staticmethod
    def test_curried_returns_a_function_that_calls_a_function_with_two_arguments_in_a_curried_manner():

        called = False

        def func2(a, b):

            nonlocal called
            called = True
            return called

        func = curried(func2)

        assert len(signature(func).parameters) == 1
        assert len(signature(func(0)).parameters) == 1
        assert func(0)
        assert called == False
        assert func(0)(0) == True
        assert called == True

    @staticmethod
    def test_curried_returns_a_function_that_calls_a_function_with_three_arguments_in_a_curried_manner():

        called = False

        def func3(a, b, c):

            nonlocal called
            called = True
            return called

        func = curried(func3)

        assert len(signature(func).parameters) == 1
        assert len(signature(func(0)).parameters) == 1
        assert len(signature(func(0)(0)).parameters) == 1
        assert func(0)
        assert called == False
        assert func(0)(0)
        assert called == False
        assert func(0)(0)(0) == True
        assert called == True
