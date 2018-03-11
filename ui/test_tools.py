import os
import pytest

from ui.tools import NameGenParser


@pytest.fixture
def name_test_file():
    # FIXME there is probably a general way to handle this.
    data_dir = os.path.join(os.path.dirname(__file__), "test", "data")
    return open(os.path.join(data_dir, "namegen.txt"))


class TestNameGen:
    def test_name_parser(self, name_test_file):
        parser = NameGenParser()
        names = parser.parse(name_test_file)

        assert len(names.first) == 2
        assert names.first[0] == "John"
        assert names.first[1] == "Jingle"

        assert len(names.last) == 3
        assert names.last[0] == "Heimer"
        assert names.last[1] == "Schmidt"
        assert names.last[2] == "Mair"  # vanity

        # FIXME
        name_test_file.close()
