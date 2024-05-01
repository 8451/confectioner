import glob
import os
import pathlib

import pytest

from confectioner import Baker


@pytest.fixture(scope="package")
def data():
    yield os.path.abspath(os.path.join(pathlib.Path(__file__).parent.resolve(), "data"))


@pytest.fixture(scope="package")
def recipe(data: str):
    yield os.path.join(data, "recipe.yml")


@pytest.fixture(scope="package")
def meals(data: str):
    yield os.path.join(data, "meals")


@pytest.fixture(scope="package")
def pantry(data: str):
    yield os.path.join(data, "pantry")


@pytest.fixture(scope="package")
def formatting(data: str):
    yield os.path.join(data, "formatting")


@pytest.fixture(scope="package")
def all_meals(meals: str):
    yield glob.glob(os.path.join(meals, "*.yml"))


@pytest.fixture(scope="package")
def all_pantry(pantry: str):
    yield glob.glob(os.path.join(pantry, "*.json"))


@pytest.fixture(scope="package")
def baker(data: str):
    return Baker(data)
