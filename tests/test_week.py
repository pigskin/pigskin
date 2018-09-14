import pytest

from pigskin.pigskin import pigskin
from pigskin.week import week


@pytest.mark.vcr()
def test_week_games():
    gp = pigskin()

    # build week object
    w = week(gp._store, 2017, 'reg', 8)

    # make sure we have a response
    assert w.games is not None

    # and that it's the right type
    assert type(w.games) is list

    # and that at least a tiny bit of the response is correct:
    assert w.games[0]['video']['title'] == 'Miami Dolphins @ Baltimore Ravens'
