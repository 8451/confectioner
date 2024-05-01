import pytest

from confectioner.templating import (
    dotted_key_exists,
    get_dotted_key,
    resolve,
    set_dotted_key,
)


def test_resolve(capsys):
    options = {
        "X": "x",
        "Y": "y",
        "N": 1,
        "D": {"A": "a", "B": "b"},
        "L": ["i0", "i1"],
        "R": "{D.A}",
    }

    assert resolve(1, options) == 1
    assert resolve("1", options) == "1"
    assert resolve("{X}", options) == "x"
    assert resolve("{N}", options) == 1
    assert resolve("{X}_{Y}", options) == "x_y"
    assert resolve("{D.A}", options) == "a"
    assert resolve("{X}-{D.B}-{N}", options) == "x-b-1"
    assert resolve(["{X}", "{Y}"], options) == ["x", "y"]
    assert resolve({"XX": "{X}"}, options) == {"XX": "x"}
    assert resolve({"XX": ["{X}"]}, options) == {"XX": ["x"]}
    assert resolve("{X}-{R}", options) == "x-a"
    assert resolve("{L.0}-{L.1}", options) == "i0-i1"
    assert resolve("{L}", options) == ["i0", "i1"]

    assert resolve({"K": "{R}"}, options, report=True)["K"] == "a"
    captured = capsys.readouterr()
    assert captured.out == "Resolving K as a\n"

    assert resolve({"K": "{R}"}, options, report=print)["K"] == "a"
    captured = capsys.readouterr()
    assert captured.out == "Resolving K as a\n"

    assert resolve(options)["R"] == resolve(options["R"], options)

    with pytest.raises(KeyError):
        resolve("{BAD_KEY}", options)

    with pytest.raises(KeyError):
        resolve("{L.2}", options)

    with pytest.raises(KeyError):
        resolve("{L.A}", options)

    with pytest.raises(KeyError):
        resolve("{D.2}", options)


def test_get_dotted_key():
    options = {"A": {"B": ["i0"]}}
    assert get_dotted_key("A.B.0", options) == "i0"
    with pytest.raises(KeyError):
        _ = get_dotted_key("A.B.1", options) == "i0"


def test_dotted_key_exists():
    options = {"A": {"B": ["i0"], "C": "c"}}
    assert dotted_key_exists("A.B.0", options)
    assert not dotted_key_exists("A.B.1", options)
    assert dotted_key_exists("A.C", options)
    assert not dotted_key_exists("A.D", options)


def test_set_dotted_key():
    d = {}

    set_dotted_key("A.B.C", "x", d)
    assert d == {"A": {"B": {"C": "x"}}}

    set_dotted_key("A.B.D", "y", d)
    assert d == {"A": {"B": {"C": "x", "D": "y"}}}
