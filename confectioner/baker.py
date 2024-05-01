import functools
import os
from typing import Optional

from . import core


class Baker:
    """
    A Baker allows you to call the functions in the core module
    with a default home directory.

    Args:
        home (str): The home directory of the baker.

    See Also: :mod:`confectioner.core`
    """

    _home: str

    def __init__(self, home: Optional[str] = None):
        self.home = home or os.getcwd()

    @property
    def home(self):
        """
        The home directory of the baker.
        """
        return self._home

    @home.setter
    def home(self, h: str):
        """
        Set the home directory of the baker.
        """
        if not isinstance(h, str):
            raise TypeError(
                f"Baker home directory must be a string but is of type {type(h)}."
            )
        h = os.path.abspath(os.path.normpath(h))
        if not os.path.isdir(h):
            raise NotADirectoryError(f"{h} is not a directory.")

        self._home = h

    @functools.wraps(core.shop)
    def shop(self, *args, **kwargs):
        kwargs.setdefault("_where", self._home)
        return core.shop(*args, **kwargs)

    @staticmethod
    @functools.wraps(core.prep)
    def prep(*args, **kwargs):
        return core.prep(*args, **kwargs)

    @staticmethod
    @functools.wraps(core.mix)
    def mix(*args, **kwargs):
        return core.mix(*args, **kwargs)

    @functools.wraps(core.bake)
    def bake(self, *args, **kwargs):
        kwargs.setdefault("_where", self._home)
        return core.bake(*args, **kwargs)
