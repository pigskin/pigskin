import os
import pytest

from pigskin.pigskin import pigskin

@pytest.mark.vcr()
def test_get_weeks():
    gp = pigskin()

    weeks_int = gp.get_weeks(2017)
    weeks_str = gp.get_weeks('2017')

    for weeks in [weeks_int, weeks_str]:
        # make sure we have a response
        assert weeks
        # and all the season types
        assert weeks['pre']
        assert weeks['reg']
        assert weeks['post']

        # make sure the week numbers look sane
        for week in weeks['pre']:
            assert int(week) >= 0 and int(week) <= 4
        for week in weeks['reg']:
            assert int(week) >= 1 and int(week) <= 17
        for week in weeks['post']:
            assert int(week) >= 18 and int(week) <= 22
