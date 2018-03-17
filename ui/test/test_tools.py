import os
import random

import pytest

from ui.tools import NameGenParser


@pytest.fixture
def name_test_file():
    # FIXME there is probably a general way to handle this.
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    return open(os.path.join(data_dir, "namegen.txt"))


@pytest.fixture()
def names(name_test_file):
    parser = NameGenParser()
    names_ = parser.parse(name_test_file)
    name_test_file.close()
    random.seed(0)
    return names_


class TestNameGen:
    def test_name_parser(self, names):
        assert 2 == len(names.male)
        assert names.male[0] == "John"
        assert names.male[1] == "Jingle"

        assert 3 == len(names.female)
        assert names.female[0] == "Jane"
        assert names.female[1] == "Tingle"
        assert names.female[2] == "Buffy"

        assert 3 == len(names.last)
        assert names.last[0] == "Heimer"
        assert names.last[1] == "Schmidt"
        assert names.last[2] == "Mair"  # vanity

    def test_male_name_generation(self, names):
        assert "Jingle Schmidt" == names.male_name()
        assert "John Schmidt" == names.male_name()
        assert "Jingle Schmidt" == names.male_name()

    def test_female_name_generation(self, names):
        assert "Tingle Schmidt" == names.female_name()
        assert "Jane Schmidt" == names.female_name()
        assert "Buffy Schmidt" == names.female_name()
