import copy
import functools
import os
import sys
import warnings
from typing import Any, Callable, Dict, List, Optional, Union

from . import templating
from .exceptions import BakeError, MixError, PrepError, ShopError
from .files import fmt, fullpath, load

# Support Python < 3.8
if sys.version_info >= (3, 8):  # pragma: nocover
    from typing import Literal
else:  # pragma: nocover
    from typing_extensions import Literal


def _norm_list(x: Union[str, List[str]]):
    if not isinstance(x, list):
        x = [x]
    return x


def _is_scalar(x: Any) -> bool:
    scalar_types = (int, float, str, bool)
    return any(isinstance(x, t) for t in scalar_types) or x is None


def _validate_kwargs(kwargs):
    for k, v in kwargs.items():
        if not _is_scalar(v):
            raise ValueError(
                f"{k} is a {type(v).__name__} but should be one of "
                f"int, float, str, bool, or None."
            )


@ShopError.catch
def shop(
    _recipe: str, _where: Optional[str] = None, _strict: bool = True, **kwargs
) -> List[str]:
    """Using a recipe, find the appropriate ingredient files

    From the recipe file, find ingredient file that match the passed
    kwargs. All other arguments are prefixed with underscores to avoid clashes
    with the keys of the recipe file.

    Parameters
    ----------
    _recipe : str
        A recipe file, either YAML or JSON
    _where : str | None, optional
        The parent directory of the recipe file. If omitted, the current
        working directory is used
    _strict : bool, optional
        If True (default) entries in the recipe only match when all keys are
        present and matching in kwargs. If False, keys not provided are
        assumed to match. For example:
        - day: friday
        - mood: angry
        would when passed (day='friday', _strict=False), but not
        (day='friday', _strict=False)
    **kwargs
        Query arguments to match against entries in the recipe

    Returns
    -------
    List[str]
        A list of ingredient files from the recipe that match the query
    """
    _validate_kwargs(kwargs)
    recipes = load(_recipe, _where)
    recipes = fmt(recipes, **kwargs)
    recipe_dir = os.path.dirname(fullpath(_recipe, _where))

    ingredients = []
    match = False

    for recipe in recipes:
        # If we are in an else block, skip if previous block has a match
        if "else" in recipe and match:
            continue

        match = all(
            (not _strict or key in kwargs)
            and (kwargs[key] in val if isinstance(val, list) else kwargs[key] == val)
            for key, val in recipe.items()
            if key not in ("ingredients", "recipes", "else")
            and (_strict or key in kwargs)
        )

        if match:
            if "ingredients" in recipe:
                _ingredients = _norm_list(recipe["ingredients"])
                ingredients.extend([fullpath(rp, recipe_dir) for rp in _ingredients])
            if "recipes" in recipe:
                sub_recipes = _norm_list(recipe["recipes"])
                for _recipe_file in sub_recipes:
                    ingredients.extend(
                        shop(_recipe_file, recipe_dir, _strict, **kwargs)
                    )

    return ingredients


@PrepError.catch
def prep(ingredients: List[str]) -> List[Dict[str, Any]]:
    """Given a list of ingredient files, load them as dictionaries

    Parameters
    ----------
    ingredients : List[str]
        A list of ingredient files

    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries, each one corresponding to an ingredient file
    """
    return list(map(load, ingredients))


@MixError.catch
def mix(
    dish: dict,
    ingredient: dict,
    dicts: Literal["overwrite", "merge"] = "merge",
    lists: Literal["overwrite", "append"] = "overwrite",
) -> dict:
    """Given two ingredients (dicts), mix (recursively merge) them.

    Parameters
    ----------
    dish : dict
        The "so-far"; what :code:`ingredient` will be mixed into
    ingredient : dict
        The new ingredient being added. If any entries exist in both this and
        :code:`dish`, then the entry here is used.
    dicts : Literal['overwrite', 'merge'], optional
        How to handle subdicts. When 'overwrite', a subdict from ingredient
        will completely clobber the corresponding entry in dish. When merge,
        the two dicts will be recursed into and merged.
    lists : Literal['overwrite', 'append'], optional
        How to handle lists. When overwrite, a list from ingredient will
        completely clobber the corresponding entry in dish. When append, if
        both entries are lists then the list from ingredient will be appended
        to the list from dish

    Returns
    -------
    dict
        A new dish (dict) with the added ingredient
    """
    dish = copy.copy(dish)
    ingredient = copy.copy(ingredient)
    if not isinstance(dish, dict) and isinstance(ingredient, dict):
        return ingredient
    for key, val in ingredient.items():
        if isinstance(val, dict) and dicts == "merge":
            dish[key] = mix(dish.get(key, {}), val, dicts=dicts, lists=lists)
        elif (
            isinstance(val, list)
            and isinstance(dish.get(key, None), list)
            and lists == "append"
        ):
            dish[key].extend(val)
        else:
            dish[key] = copy.copy(val)

    return dish


@functools.singledispatch
@BakeError.catch
def bake(
    _recipe: Union[str, List[Dict[str, Any]]],
    *,
    _reverse: bool = False,
    _dicts: Literal["overwrite", "merge"] = "merge",
    _lists: Literal["overwrite", "append"] = "overwrite",
    _resolve: bool = True,
    _eager: bool = False,
    _report: Union[bool, Callable] = False,
    _where: Optional[str] = None,
    _strict: bool = True,
    **kwargs,
) -> Dict[str, Any]:
    """Bake (merge) a set of ingredients into a finished product (dictionary).

    Bake can either do the entire confecting process from end to end (shop,
    prep, bake), or can take the list of prepped ingredient dictionaries and
    just do the final step (recursively merge). All arguments other than the
    first one (:code:`_recipe`) are keyword-only. All arguments are prefixed
    with underscores to avoid clashes with the keys of the recipe file.

    Parameters
    ----------
    _recipe : str | List[Dict[str, Any]]
        Either a path to a recipe file or the list of dicts output by prep
    _reverse : bool, optional
        If False (default) ingredients at end of list take precedence. If True,
        ingredients at top take precedence.
    _dicts : Literal['overwrite', 'merge'], optional
        See (:func:`confectioner.core.mix`)
    _lists : Literal['overwrite', 'append'], optional
        See (:func:`confectioner.core.mix`)
    _resolve : bool, optional
        If True (default) resolve ony entries with templating syntax.
    _eager : bool, optional
        If True (default False) eagerly resolve templating syntax. (i.e. if
        config B is being mixed into config A, resolve A on itself before
        mixing B into A)
    _report : bool | Callable, optional
        Should any informational messages be logged. Boolean or a callable
        that performs the logging (such as :code:`print`)
    _where : str | None, optional
        See (:func:`confectioner.core.shop`). Ignored if :code:`_recipe`
        is not a filepath.
    _strict : bool, optional
        See (:func:`confectioner.core.shop`) Ignored if :code:`_recipe`
        is not a filepath.
    **kwargs
        See (:func:`confectioner.core.shop`) Ignored if :code:`_recipe`
        is not a filepath.

    Returns
    -------
    Dict[str, Any]
    """
    raise NotImplementedError(
        "Bake takes either a list of dictionaries or a path to a recipe file."
    )


@bake.register(list)
def _bake_list(
    _recipe: List[Dict[str, Any]],
    *,
    _reverse: bool = False,
    _dicts: Literal["overwrite", "merge"] = "merge",
    _lists: Literal["overwrite", "append"] = "overwrite",
    _resolve: bool = True,
    _eager: bool = False,
    _report: Union[bool, Callable] = False,
    **kwargs,
) -> Dict[str, Any]:
    if _eager and not _resolve:
        warnings.warn("_eager=True is ignored when _resolve=False")

    ingredients = list(reversed(_recipe)) if _reverse else _recipe

    def resolving_function(
        left: Dict[str, Any], right: Dict[str, Any]
    ) -> Dict[str, Any]:
        return mix(
            (
                left
                if not (_eager and _resolve)
                else templating.resolve(left, remove_escapes=False)
            ),
            right,
            dicts=_dicts,
            lists=_lists,
        )

    dessert = functools.reduce(resolving_function, ingredients)

    if _resolve:
        dessert = templating.resolve(dessert, dessert, report=_report)

    return dessert


@bake.register(str)
def _bake_str(
    _recipe: str,
    *,
    _reverse: bool = False,
    _dicts: Literal["overwrite", "merge"] = "merge",
    _lists: Literal["overwrite", "append"] = "overwrite",
    _where: Optional[str] = None,
    _strict: bool = True,
    _resolve: bool = True,
    _eager: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    ingredients = shop(_recipe=_recipe, _where=_where, _strict=_strict, **kwargs)

    prepped = prep(ingredients)

    baked = bake(
        prepped,
        _reverse=_reverse,
        _dicts=_dicts,
        _lists=_lists,
        _resolve=_resolve,
        _eager=_eager,
    )

    return baked
