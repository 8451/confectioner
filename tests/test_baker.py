import os

import pytest

from confectioner import Baker
from confectioner.files import load


def test_home(data: str, pantry: str, recipe: str):
    baker = Baker()

    assert baker.home == os.getcwd()

    with pytest.raises(TypeError):
        baker.home = None
    with pytest.raises(NotADirectoryError):
        baker.home = recipe

    baker.home = data
    baker2 = Baker(pantry)
    assert baker.home == data
    assert baker2.home == pantry


def test_shop(baker: Baker, pantry: str):
    assert baker.shop("recipe.yml") == [os.path.join(pantry, "water.json")]


def test_prep(baker: Baker, pantry: str):
    shopped = baker.shop("recipe.yml")
    assert baker.prep(shopped) == [load(os.path.join(pantry, "water.json"))]


def test_mix(baker: Baker):
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 20, "c": 30}

    assert baker.mix(d1, d2) == {"a": 1, "b": 20, "c": 30}


def test_bake(baker: Baker, pantry: str):
    assert baker.bake("recipe.yml") == load(os.path.join(pantry, "water.json"))
