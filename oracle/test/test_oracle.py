import pytest

from oracle import DummyDelphi
from oracle.oracle import OracleController


@pytest.fixture
def oracle_controller(campaign_db, oracle_db, provider):
    fooproviders = {'foo': provider}
    controller = OracleController(DummyDelphi(), campaign_db, oracle_db,
                                  fooproviders)
    return controller


class TestOracleController:
    """
    Integration tests for the oracle controller.
    """

    def test_index_note(self, note, oracle_controller):
        old_index_complete = oracle_controller.index_complete

        def new_index_complete(*args):
            old_index_complete(*args)
            assert len(oracle_controller.pending) == 0
            assert 'foo' in oracle_controller.providers
            assert len(oracle_controller.notemap) == 1
            assert 1 in oracle_controller.notemap

        oracle_controller.index_complete = new_index_complete
        oracle_controller.index_note(note)
