import os
import pytest

from pigskin.pigskin import pigskin


@pytest.mark.vcr()
def test_get_game_streams():
    gp = pigskin()
    assert gp.login(username=pytest.gp_username, password=pytest.gp_password)

    season = 2017
    season_type = 'reg'
    week = '8'

    games = gp.get_games(season, season_type, week)
    assert games

    game_id = games[1]['gameId'] # grab a game_id

    versions = gp.get_game_versions(game_id, season)
    assert versions

    streams = gp.get_game_streams(versions['Condensed game'])
    assert streams

    # and check that there's actual links provided
    for f in ['hls', 'chromecast', 'connecttv']:
        assert 'https://' in streams[f]


@pytest.mark.vcr()
def test_get_nfl_network_streams():
    gp = pigskin()
    assert gp.login(username=pytest.gp_username, password=pytest.gp_password)

    streams = gp.get_nfl_network_streams()

    # make sure we have responses
    assert streams

    # and check that there's actual links provided
    for f in ['hls', 'chromecast', 'connecttv']:
        assert 'https://' in streams[f]


# TODO: run this when redzone live is actually broadcasting
#@pytest.mark.vcr()
#def test_get_redzone_streams():
#    gp = pigskin()
#    assert gp.login(username=pytest.gp_username, password=pytest.gp_password)
#
#    streams = gp.get_redzone_streams()
#
#    # make sure we have responses
#    assert streams
#
#    # and check that there's actual links provided
#    for f in ['hls', 'chromecast', 'connecttv']:
#        assert 'https://' in streams[f]


@pytest.mark.vcr()
def test_get_redzone_streams_failure():
    gp = pigskin()
    assert gp.login(username=pytest.gp_username, password=pytest.gp_password)

    streams = gp.get_redzone_streams()

    # make sure we don't have a response
    assert not streams


@pytest.mark.vcr()
def test__get_diva_config():
    gp = pigskin()
    diva_config_url = gp.config['modules']['DIVA']['HTML5']['SETTINGS']['Live24x7']

    diva_config = gp._get_diva_config(diva_config_url)

    # check our response
    assert diva_config
    assert diva_config['processing_url']
    assert diva_config['video_data_url']


@pytest.mark.vcr()
def test__build_processing_url_payload():
    gp = pigskin()
    assert gp.login(username=pytest.gp_username, password=pytest.gp_password)

    video_id = 'this_is_a_video_id'
    vs_url = 'https://this.is.a.video.source.url'

    response = gp._build_processing_url_payload(video_id, vs_url)

    assert response
    assert video_id in response
    assert vs_url in response
