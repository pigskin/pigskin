import os
import pytest

from pigskin.pigskin import pigskin

@pytest.mark.vcr()
def test_get_seasons():
    gp = pigskin()

    seasons = gp.get_seasons()

    # make sure we have a response
    assert seasons

    # make sure it's sorted high to low
    assert seasons == sorted(seasons, reverse=True)

    # make sure the seasons look sane-ish
    for i in seasons:
        assert int(i) > 2000 and int(i) < 2050


@pytest.mark.vcr()
def test_get_seasons_failure():
    gp = pigskin()

    # change to a wrong URL
    gp.config['modules']['ROUTES_DATA_PROVIDERS']['games'] = 'https://httpbin.org/json'
    seasons = gp.get_seasons()

    # make sure we don't have a response
    assert not seasons

    # another wrong URL
    gp.config['modules']['ROUTES_DATA_PROVIDERS']['games'] = 'https://httpbin.org/html'
    seasons = gp.get_seasons()

    # make sure we have a response
    assert not seasons
