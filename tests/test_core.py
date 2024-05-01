import os
from typing import List

import pytest

from confectioner import bake, mix, prep, shop
from confectioner.exceptions import BakeError, ShopError
from confectioner.files import load


def test_shop(
    recipe: str, pantry: str, all_pantry: List[str], formatting: str, data: str
):
    # No kwargs only returns water
    assert shop(recipe) == [os.path.join(pantry, "water.json")]

    # Not strict returns everything in pantry
    assert set(shop(recipe, _strict=False)) == set(all_pantry)

    # On the weekends we drink wine
    wine_and_water = [
        os.path.join(pantry, food) for food in ("water.json", "wine.json")
    ]
    assert set(shop(recipe, day="Friday")) == set(wine_and_water)
    assert set(shop(recipe, day="Saturday")) == set(wine_and_water)

    # When microwaving dinner we eat easy mac
    water_and_easymac = [
        os.path.join(pantry, food) for food in ("water.json", "easy-mac.json")
    ]
    assert set(shop(recipe, microwave=True)) == set(water_and_easymac)
    assert set(shop(recipe, microwave=True, day="Friday")) == set(
        water_and_easymac + [os.path.join(pantry, "wine.json")]
    )

    # When not microwaving we eat a burger with a salad
    dinner_base = [
        os.path.join(pantry, food)
        for food in (
            "water.json",
            "bun.json",
            "patty.json",
            "toppings.json",
            "lettuce.json",
            "dressing.json",
        )
    ]
    spice_burger_weekend = dinner_base + [
        os.path.join(pantry, food) for food in ("wine.json", "jalepenos.json")
    ]
    lunch_combo = [
        os.path.join(pantry, food)
        for food in (
            "water.json",
            "soda.json",
            "bun.json",
            "patty.json",
            "toppings.json",
        )
    ]

    assert set(shop(recipe, microwave=False)) == set(dinner_base)
    assert set(shop(recipe, microwave=False, spicy=True, day="Saturday")) == set(
        spice_burger_weekend
    )
    assert set(shop(recipe, combo="lunch")) == set(lunch_combo)

    # If we pass a non-scalar value to shop should get an error
    with pytest.raises(ShopError):
        shop(recipe, non_scalar=[])

    # Test formatted configs
    assert shop(os.path.join(formatting, "recipe.yml"), val="formatted") == [
        os.path.join(formatting, "formatted.json")
    ]

    # Test else blocks
    assert set(shop(os.path.join(data, "else/recipe.yml"), day="friday")) == set(
        os.path.join(data, "else", file) for file in ("wine.json", "plate.json")
    )
    assert set(
        shop(os.path.join(data, "else/recipe.yml"), day="tuesday", treat=True)
    ) == set(
        os.path.join(data, "else", file) for file in ("lemonade.json", "plate.json")
    )
    assert set(shop(os.path.join(data, "else/recipe.yml"), day="tuesday")) == set(
        os.path.join(data, "else", file) for file in ("water.json", "plate.json")
    )


def test_prep(pantry: str):
    foods = [os.path.join(pantry, food) for food in ("water.json", "wine.json")]

    expected = [load(food) for food in foods]

    assert prep(foods) == expected


def test_mix():
    d1 = {"a": 1, "b": 2, "nested": {"x": 24, "y": 25, "lst": [1, 2, 3]}}

    d2 = {"a": 10, "c": 30, "nested": {"x": 240, "z": 260, "lst": [4, 5, 6]}}

    # Default to merge dicts and overwrite lists
    assert mix(d1, d2) == {
        "a": 10,
        "b": 2,
        "c": 30,
        "nested": {"x": 240, "y": 25, "z": 260, "lst": [4, 5, 6]},
    }

    # If we overwrite dicts
    assert mix(d1, d2, dicts="overwrite") == {
        "a": 10,
        "b": 2,
        "c": 30,
        "nested": {"x": 240, "z": 260, "lst": [4, 5, 6]},
    }

    # If we append lists
    assert mix(d1, d2, lists="append") == {
        "a": 10,
        "b": 2,
        "c": 30,
        "nested": {"x": 240, "y": 25, "z": 260, "lst": [1, 2, 3, 4, 5, 6]},
    }


def test_bake_list(pantry: str):
    ingredients = prep(
        [
            os.path.join(pantry, food)
            for food in ("water.json", "bun.json", "patty.json")
        ]
    )

    assert bake(ingredients) == {
        "beverage": "water",
        "burger": {"bun": "sesame", "patty": "angus"},
    }

    weekend = ingredients + prep([os.path.join(pantry, "wine.json")])

    assert bake(weekend) == {
        "beverage": "wine",
        "burger": {"bun": "sesame", "patty": "angus"},
    }

    assert bake(weekend, _reverse=True) == {
        "beverage": "water",
        "burger": {"bun": "sesame", "patty": "angus"},
    }


def test_bake_str(recipe: str):
    # No kwargs only returns water
    assert bake(recipe) == {"beverage": "water"}
    assert bake(recipe, day="Friday") == {"beverage": "wine"}
    assert bake(recipe, microwave=True) == {
        "beverage": "water",
        "main": {"name": "mac & cheese", "toppings": "hot sauce"},
    }
    assert bake(recipe, microwave=False, day="Friday", spicy=True, _lists="append") == {
        "beverage": "wine",
        "salad": {"lettuce": "romaine", "dressing": "caesar"},
        "burger": {
            "bun": "sesame",
            "patty": "angus",
            "toppings": [
                "american cheese",
                "mayo",
                "mustard",
                "lettuce",
                "tomato",
                "pickles",
                "jalepenos",
            ],
        },
    }


def test_bake_other():
    with pytest.raises(BakeError):
        bake(None)


def test_bake_eager():
    ingredients = [{"A": {"X": 1}, "B": "{A}"}, {"B": {"Y": 2}}]

    assert bake(ingredients)["B"] == {"Y": 2}
    assert bake(ingredients, _eager=True)["B"] == {"X": 1, "Y": 2}

    with pytest.warns():
        assert bake(ingredients, _eager=True, _resolve=False)["B"] == {"Y": 2}
