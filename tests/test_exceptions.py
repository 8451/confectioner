import pytest

from confectioner.exceptions import BakeError, ShopError


def test_confect_error():
    @BakeError.catch
    def passes():
        return True

    @BakeError.catch
    def fails_shop():
        raise ShopError()

    @BakeError.catch
    def fails_other():
        raise ValueError()

    assert passes()

    with pytest.raises(ShopError):
        fails_shop()

    with pytest.raises(BakeError):
        fails_other()

    assert str(BakeError()) == ""
    assert str(BakeError(ValueError("msg"))) == "ValueError - msg"
