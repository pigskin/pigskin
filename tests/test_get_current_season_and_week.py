import os
import pytest

from pigskin.pigskin import pigskin

@pytest.mark.vcr()
def test_get_current_season_and_week():
    gp = pigskin()
    gp.login(username=pytest.gp_username, password=pytest.gp_password)

    current = gp.get_current_season_and_week()

    # make sure we have a response
    assert current

    # that the fields are there and set
    assert current['season']
    assert current['season_type']
    assert current['week']

    # and that the data format remains stable and sane-ish
    assert int(current['season']) > 2000 and int(current['season']) < 2050
    assert current['season_type'] in {'pre', 'reg', 'post'}
    assert int(current['week']) > 0 and int(current['week']) < 23


@pytest.mark.vcr()
def test_get_current_season_and_week_failure():
    gp = pigskin()
    gp.login(username=pytest.gp_username, password=pytest.gp_password)

    # change to a wrong URL
    gp.config['modules']['ROUTES_DATA_PROVIDERS']['games'] = 'https://httpbin.org/json'
    current = gp.get_current_season_and_week()

    # make sure we have no answer
    assert not current

    # another wrong URL
    gp.config['modules']['ROUTES_DATA_PROVIDERS']['games'] = 'https://httpbin.org/html'
    current = gp.get_current_season_and_week()

    # make sure we have no answer
    assert not current
