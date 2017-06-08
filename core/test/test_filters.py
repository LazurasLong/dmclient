from core import filters


def test_join():
    assert filters.join(filters.campaign, filters.any) == "{};;{}".format(
        filters.campaign, filters.any)
