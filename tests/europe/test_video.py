import pytest
import vcr

from pigskin.pigskin import pigskin


@pytest.fixture(scope='class')
def gp():
    with vcr.use_cassette('backends/europe/gp.yaml'):
        return pigskin()


@pytest.mark.incremental
class TestEuropeVideo(object):
    """These don't require authentication to Game Pass."""
    @vcr.use_cassette('backends/europe/video__get_diva_config.yaml')
    @staticmethod
    def test__get_diva_config(gp):
        diva_config_url = gp._store.gp_config['modules']['DIVA']['HTML5']['SETTINGS']['Live24x7']

        diva_config = gp._video._get_diva_config(diva_config_url)

        # check the response
        assert diva_config
        assert diva_config['processing_url']
        assert diva_config['video_data_url']


@pytest.mark.incremental
class TestEuropeVideoAuth(object):
    """These require authentication to Game Pass"""
    @vcr.use_cassette('backends/europe/video_auth_login.yaml')
    @staticmethod
    def test_login(gp):
        assert gp.login(pytest.gp_username, pytest.gp_password, force=True)

        # make sure tokens are actually set
        assert gp._store.access_token
        assert gp._store.refresh_token


    @staticmethod
    def test__build_processing_url_payload(gp):
        video_id = 'this_is_a_video_id'
        vs_url = 'https://this.is.a.video.source.url'

        response = gp._video._build_processing_url_payload(video_id, vs_url)

        assert response
        for i in [video_id, vs_url, gp._store.access_token]:
            assert i in response


    @vcr.use_cassette('backends/europe/video_auth_nfln_streams.yaml')
    @staticmethod
    def test_get_nfl_network_streams(gp):
        streams = gp._video.get_nfl_network_streams()

        # make sure we have responses
        assert streams

        # and check that there's actual links provided
        for f in ['hls', 'chromecast', 'connecttv']:
            assert streams[f]
            assert 'https://' in streams[f]


    # TODO: run this when redzone live is actually broadcasting
    #@vcr.use_cassette('backends/europe/video_auth_redzone_streams_broadcasting.yaml')
    #@staticmethod
    #def test_get_nfl_network_streams(gp):
    #    streams = gp.get_redzone_streams()

    #    # make sure we have responses
    #    assert streams

    #    # and check that there's actual links provided
    #    for f in ['hls', 'chromecast', 'connecttv']:
    #        assert streams[f]
    #        assert 'https://' in streams[f]


    @vcr.use_cassette('backends/europe/video_auth_redzone_streams_not_broadcasting.yaml')
    @staticmethod
    def test_get_redzone_streams_failure(gp):
        streams = gp._video.get_redzone_streams()

        # make sure we don't have a response
        assert not streams


    #TODO: enable and record when it is broadcasting
    #@vcr.use_cassette('backends/europe/video_auth_redzone_on_air_yep.yaml')
    #@staticmethod
    #def test_is_redzone_on_air(gp):
    #    assert gp.is_redzone_on_air()


    @vcr.use_cassette('backends/europe/video_auth_redzone_on_air_nope.yaml')
    @staticmethod
    def test_is_redzone_on_air_nope(gp):
        assert gp.is_redzone_on_air() is False
