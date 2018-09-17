import pytest

from pigskin.pigskin import pigskin


# TODO: test live game stream
#def test_get_game_streams_live():

@pytest.mark.vcr()
def test_get_nfl_network_streams():
    gp = pigskin()
    assert gp.login(username=pytest.gp_username, password=pytest.gp_password)

    streams = gp._video.get_nfl_network_streams()

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

    streams = gp._video.get_redzone_streams()

    # make sure we don't have a response
    assert not streams
