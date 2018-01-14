import pytest
from PyQt5.QtGui import QValidator


class TestIDValidator:
    @pytest.mark.parametrize("input", ["foo", "FOO", "Foo"])
    def test_validate_valid(self, id_validator, input):
        assert id_validator.validate(input, 0) == QValidator.Acceptable

    @pytest.mark.parametrize("input", [" ", "  F", "*", "!", "<", "🐱"])
    def test_validate_invalid(self, id_validator, input):
        assert id_validator.validate(input, 0) == QValidator.Invalid

    @pytest.mark.parametrize("input,fixed", zip(["Foo", "foo"], ["FOO", "FOO"]))
    def test_fixup(self, id_validator, input, fixed):
        assert id_validator.fixup(input) == fixed
