import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Optional, Set, Union


@dataclass(frozen=True)
class _ResolveReporter:
    report: bool = False
    resolved: bool = False
    key: str = ""
    logger: Callable = print

    def add_key(self, new_key: Union[str, int]) -> "_ResolveReporter":
        return _ResolveReporter(
            self.report,
            self.resolved,
            f"{self.key}.{new_key}" if self.key else str(new_key),
            self.logger,
        )

    def mark_resolved(self) -> "_ResolveReporter":
        return _ResolveReporter(self.report, True, self.key, self.logger)

    def log(self, value):
        if self.report and self.key and self.resolved:
            self.logger(f"Resolving {self.key} as {value}")


def resolve(
    o: Any,
    options: Optional[Mapping[str, Any]] = None,
    *,
    report: Union[_ResolveReporter, bool, Callable] = False,
    remove_escapes: bool = True,
) -> Any:
    """
    Resolve templated values (possibly recursively).

    Parameters
    ----------
    o : Any
        The object to resolve.
    options : Mapping[str, Any] | None, optional
        The options to lookup resolved values in.
        If None, use `o` as the options.
    report : _ResolveReporter | bool | Callable, optional
        If True, print a message for each resolved value.
        If False, do not print messages.
        If a callable, call the callable for each resolved value.
    remove_escapes : bool, optional
        If True (default), remove escape characters from resolved strings.

    Returns
    -------
    Any
        The resolved object.
    """
    if isinstance(report, bool):
        report = _ResolveReporter(report)
    elif callable(report):
        report = _ResolveReporter(True, logger=report)

    if options is None:
        options = o

    if isinstance(o, Mapping):
        return {
            k: resolve(
                v, options, report=report.add_key(k), remove_escapes=remove_escapes
            )
            for k, v in o.items()
        }
    elif isinstance(o, list):
        return [
            resolve(v, options, report=report.add_key(i), remove_escapes=remove_escapes)
            for i, v in enumerate(o)
        ]
    elif isinstance(o, str) and _single_dotted_key(o):
        val = get_dotted_key(find_template_keys(o).pop(), options)
        report = report.mark_resolved()
        return resolve(val, options, report=report, remove_escapes=remove_escapes)
    elif isinstance(o, str) and find_template_keys(o):
        for match in find_template_keys(o):
            val = str(get_dotted_key(match, options))
            o = o.replace(f"{{{match}}}", val)

        report = report.mark_resolved()

        return resolve(o, options, report=report, remove_escapes=remove_escapes)
    else:
        if isinstance(o, str) and remove_escapes:
            o = o.replace("\\{", "{").replace("\\}", "}")
        report.log(o)
        return o


def get_dotted_key(dotted: str, options: Union[Mapping[str, Any], list]) -> Any:
    """
    Get a nested value from a dictionary or list using a dotted key.

    Parameters
    ----------
    dotted : str
        The dotted key to lookup.
    options : Mapping[str, Any] | list
        The dictionary or list to lookup the dotted key in.

    Returns
    -------
    Any
        The value at the dotted key.
    """
    key: Union[str, int]
    rest: Optional[str]

    split = dotted.split(".", 1)
    key = split[0]
    rest = None if len(split) == 1 else split[1]

    try:
        key = int(key)
    except ValueError:
        pass

    if (isinstance(key, int) and isinstance(options, Mapping)) or (
        isinstance(key, str) and isinstance(options, list)
    ):
        raise KeyError(dotted)
    try:
        if rest is None:
            return options[key]  # type: ignore
        else:
            return get_dotted_key(rest, options[key])  # type: ignore
    except (KeyError, IndexError):
        raise KeyError(dotted)


def set_dotted_key(dotted: str, val: Any, options: Dict[str, Any]) -> None:
    """
    Set a nested value in a dictionary or list using a dotted key.

    Parameters
    ----------
    dotted : str
        The dotted key to set.
    options : Dict[str, Any]
        The dictionary or list to set the dotted key in.

    Returns
    -------
    None
    """
    key: Union[str, int]
    rest: Optional[str]

    split = dotted.split(".", 1)
    key = split[0]
    rest = None if len(split) == 1 else split[1]

    if rest is None:
        options[key] = val
    else:
        options.setdefault(key, {})
        set_dotted_key(rest, val, options[key])


def dotted_key_exists(dotted: str, options: Union[Mapping[str, Any], list]) -> bool:
    """
    Check if a dotted key exists in a dictionary or list.

    Parameters
    ----------
    dotted : str
        The dotted key to check.
    options : Mapping[str, Any] | list
        The dictionary or list to check the dotted key in.

    Returns
    -------
    bool
        True if the dotted key exists, False otherwise.
    """
    try:
        get_dotted_key(dotted, options)
    except (KeyError, IndexError):
        return False

    return True


def find_template_keys(o: str) -> Set[str]:
    """
    Find all template keys in a string.

    Parameters
    ----------
    o : str
        The string to search.

    Returns
    -------
    Set[str]
        The set of template keys.
    """
    return set(re.findall(r"(?<!\\){([^\\]*?)}", o))


def _single_dotted_key(o: str):
    template_keys = find_template_keys(o)
    if len(template_keys) != 1:
        return False
    return o == "{" + template_keys.pop() + "}"
