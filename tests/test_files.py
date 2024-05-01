import os

import pytest

from confectioner.files import (
    _load_yaml,
    fullpath,
    load,
    register_loader,
    register_reader,
)


def test_fullpath():
    assert fullpath("recipe.yml") == os.path.join(os.getcwd(), "recipe.yml")


def test_load(meals: str, pantry: str):
    assert load(os.path.join(meals, "salad.yml")) == [
        {"ingredients": ["../pantry/lettuce.json", "../pantry/dressing.json"]}
    ]

    assert load(os.path.join(pantry, "water.json")) == {"beverage": "water"}

    with pytest.raises(ValueError):
        load("unsupportedextension.conf")


def test_register(recipe: str):
    reader_used = False
    loader_used = False

    def reader(path: str):
        nonlocal reader_used
        reader_used = True
        return open(path)

    def loader(io):
        nonlocal loader_used
        loader_used = True
        return _load_yaml(io)

    with pytest.raises(ValueError):
        register_reader("file", reader)

    with pytest.raises(ValueError):
        register_loader(".json", loader)

    recipe_contents_1 = load(recipe)
    assert not reader_used
    assert not loader_used

    register_reader("file", reader, force=True)
    register_loader(".yml", loader, force=True)

    recipe_contents_2 = load(recipe)
    assert reader_used
    assert loader_used
    assert recipe_contents_1 == recipe_contents_2
