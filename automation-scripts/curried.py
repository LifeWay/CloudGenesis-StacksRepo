from functools import partial
from inspect import signature

def curried(func):

    """
    A decorator that converts a multi-parameter function into a set of single-parameter functions

    :param func: The function to convert
    :return: A curried version of the specified function
    """

    def inner(arg):

        """
        The inner function that curries the first parameter of a function to that function

        :param arg: The parameter to curry to this function
        :return: The function with the parameter curried to it
        """

        # Query for the number of parameters for this function
        if len(signature(func).parameters) == 1:

            # Simply call single parameter functions
            return func(arg)

        else:

            # Curry the first parameter to the specified function with the partial function
            # and recurse for the subsequent parameters, if any
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
