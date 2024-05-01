import functools
import sys
from typing import Callable, Optional, TypeVar

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec  # pragma: no cover
else:
    from typing import ParamSpec  # pragma: no cover


P = ParamSpec("P")
R = TypeVar("R")


class ConfectionerError(Exception):
    caught: Optional[Exception]

    def __init__(self, caught: Optional[Exception] = None):
        self.caught = caught

        super().__init__(caught)

    def __str__(self):
        return (
            f"{self.caught.__class__.__name__} - {self.caught}" if self.caught else ""
        )

    @classmethod
    def catch(cls, f: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(f)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            # noinspection PyBroadException
            try:
                return f(*args, **kwargs)
            except ConfectionerError as e:
                raise e
            except Exception as e:
                raise cls from e

        return wrapped


class ShopError(ConfectionerError):
    pass


class PrepError(ConfectionerError):
    pass


class MixError(ConfectionerError):
    pass


class BakeError(ConfectionerError):
    pass
