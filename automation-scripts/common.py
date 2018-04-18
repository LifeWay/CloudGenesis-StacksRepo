class Struct:

    """
    Allows a generic class to be created with fields backed by internal __dict__ instance
    """

    def __init__(self, **entries): self.__dict__.update(entries)

    def __eq__(self, other): return self.__dict__ == other.__dict__

    def __neq__(self, other): return self.__dict__ != other.__dict__

    def __repr__(self): return repr(self.__dict__)

    def __str__(self): return str(self.__dict__)

