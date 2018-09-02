import pytest
import requests

from pigskin.pigskin import pigskin

gp = pigskin()


@pytest.mark.vcr()
def test_invalid_response_get_json():
    gp.config['modules']['API'] = { key: 'https://httpbin.org/json' for key in gp.config['modules']['API'] }
    gp.config['modules']['ROUTES_DATA_PROVIDERS'] = { key: 'https://httpbin.org/json' for key in gp.config['modules']['ROUTES_DATA_PROVIDERS'] }

    assert not gp.get_current_season_and_week()
    assert not gp.get_seasons()
    assert not gp.get_weeks(2017)
    assert not gp.get_games(2017, 'reg', 8)

@pytest.mark.vcr()
def test_invalid_response_get_html():
    gp.config['modules']['API'] = { key: 'https://httpbin.org/html' for key in gp.config['modules']['API'] }
    gp.config['modules']['ROUTES_DATA_PROVIDERS'] = { key: 'https://httpbin.org/html' for key in gp.config['modules']['ROUTES_DATA_PROVIDERS'] }

    assert not gp.get_current_season_and_week()
    assert not gp.get_seasons()
    assert not gp.get_weeks(2017)
    assert not gp.get_games(2017, 'reg', 8)

@pytest.mark.vcr()
def test_invalid_response_get_bytes():
    gp.config['modules']['API'] = { key: 'https://httpbin.org/bytes/20' for key in gp.config['modules']['API'] }
    gp.config['modules']['ROUTES_DATA_PROVIDERS'] = { key: 'https://httpbin.org/bytes/20' for key in gp.config['modules']['ROUTES_DATA_PROVIDERS'] }

    assert not gp.get_current_season_and_week()
    assert not gp.get_seasons()
    assert not gp.get_weeks(2017)
    assert not gp.get_games(2017, 'reg', 8)

@pytest.mark.vcr()
def test_invalid_response_post_json():
    gp.config['modules']['API'] = { key: 'https://httpbin.org/post' for key in gp.config['modules']['API'] }
    gp.config['modules']['ROUTES_DATA_PROVIDERS'] = { key: 'https://httpbin.org/post' for key in gp.config['modules']['ROUTES_DATA_PROVIDERS'] }

    # these POST, and as far as I can tell, httbin only provides JSON responses to POST
    # TODO: find a way to test these for html and bytes as well
    assert not gp.login(username='nope', password='so_secret')
    assert not gp.refresh_tokens()
