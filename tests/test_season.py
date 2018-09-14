import pytest
from collections import OrderedDict

from pigskin.pigskin import pigskin
from pigskin.pigskin import season

@pytest.mark.vcr()
def test_season_weeks():
    gp = pigskin()

    # build season object
    s = season(gp._store, 2017)

    # make sure we have a response
    assert s.weeks is not None

    assert type(s.weeks) is OrderedDict

    # and all the season types are there
    assert s.weeks['pre']
    assert s.weeks['reg']
    assert s.weeks['post']

    # make sure the week numbers look sane
    for week in s.weeks['pre']:
        assert int(week) >= 0 and int(week) <= 4
    for week in s.weeks['reg']:
        assert int(week) >= 1 and int(week) <= 17
    for week in s.weeks['post']:
        assert int(week) >= 18 and int(week) <= 22
