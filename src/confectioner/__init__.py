from . import _version
from .baker import Baker
from .core import bake, mix, prep, shop

__version__ = _version.__version__


__doc__ = """
Confect - A Modular Config Framework for Python Applications
============================================================
"""

__all__ = ["shop", "prep", "mix", "bake", "Baker"]
