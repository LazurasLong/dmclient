import pytest

from ui.game.system import SystemIDValidator


@pytest.fixture(scope="module")
def game_system():
    return ["foo"]


@pytest.fixture(scope="module")
def id_validator(game_system):
    return SystemIDValidator(game_system)


