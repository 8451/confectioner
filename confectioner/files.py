import json
import os
from typing import IO, Any, Callable, Dict, Optional, TypeVar

import yaml

T = TypeVar("T")


##############################################################################
# Reading Files
##############################################################################
_READERS: Dict[str, Callable[[str], IO]] = {
    "file": open,
}


def register_reader(
    protocol: str, reader: Callable[[str], IO], force: bool = False
) -> None:
    """
    Register a reader for a protocol.

    Parameters
    ----------
    protocol : str
        The protocol to register the reader for.
    reader : Callable[[str], IO]
        The reader function.
    force : bool, optional
        If True, override an existing reader for that protocol
        (if it exists). If False (default), raise a ValueError.

    Returns
    -------
    None
    """
    protocol = protocol.lower().rstrip(":/")
    global _READERS
    if protocol in _READERS and not force:
        raise ValueError(f"Reader for {protocol} already exists")
    _READERS[protocol] = reader


def _get_protocol(path: str):
    try:
        protocol, _ = path.split("://", 1)
    except ValueError:
        protocol = "file"
    return protocol


def _is_local(path: str):
    return _get_protocol(path) == "file"


def _open(path: str) -> IO:
    return _READERS[_get_protocol(path)](path)


##############################################################################
# Loading (Parsing) Files
##############################################################################
def _load_yaml(io: IO) -> Any:
    return yaml.load(io, yaml.Loader)


def _load_json(io: IO) -> Any:
    return json.load(io)


_LOADERS: Dict[str, Callable[[IO], Any]] = {
    ".yaml": _load_yaml,
    ".yml": _load_yaml,
    ".json": _load_json,
    ".jsn": _load_json,
}


def register_loader(
    extension: str, loader: Callable[[IO], Any], force: bool = False
) -> None:
    """
    Register a loader for a file extension.

    Parameters
    ----------
    extension : str
        The file extension to register the loader for.
    loader : Callable[[IO], Any]
        The loader function.
    force : bool, optional
        If True, override an existing loader for that file extension
        (if it exists). If False (default), raise a ValueError.

    Returns
    -------
    None
    """
    extension = f'.{extension.lstrip(".")}'
    global _LOADERS
    if extension in _LOADERS and not force:
        raise ValueError(f"Loader for {extension} already exists")
    _LOADERS[extension] = loader


def _get_loader(path: str) -> Callable[[IO], Any]:
    ext = os.path.splitext(path)[1].lower()

    try:
        return _LOADERS[ext]
    except KeyError:
        raise ValueError(f"Unsupported extension {ext}")


##############################################################################
# Public Functions
##############################################################################
def fullpath(relpath: str, where: Optional[str] = None):
    where = where or os.getcwd()

    if _is_local(relpath) and not os.path.isabs(relpath):
        return os.path.normpath(os.path.join(where, relpath))
    else:
        return relpath


def load(_path: str, _where: Optional[str] = None) -> Any:
    _path = fullpath(relpath=_path, where=_where)

    loader = _get_loader(_path)

    with _open(_path) as io:
        return loader(io)


def fmt(recipe: T, **kwargs) -> T:
    if isinstance(recipe, list):
        return [fmt(r, **kwargs) for r in recipe]  # type: ignore [return-value]
    elif isinstance(recipe, dict):
        return {  # type: ignore [return-value]
            k: fmt(v, **kwargs) for k, v in recipe.items()
        }
    elif isinstance(recipe, str):
        return recipe.format(**kwargs)  # type: ignore [return-value]
    else:
        return recipe
