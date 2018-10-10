import pytest
import vcr


try:  # Python 2.7
    # requests's ``json()`` function returns strings as unicode (as per the
    # JSON spec). In 2.7, those are of type unicode rather than str. basestring
    # was created to help with that.
    # https://docs.python.org/2/library/functions.html#basestring
    basestring = basestring
except NameError:
    basestring = str


@pytest.mark.incremental
class TestBroadcast(object):
    """These don't require authentication to Game Pass."""
    @vcr.use_cassette('public_API/europe_broadcast.yaml')
    @staticmethod
    def test_desc(gp):
        for b in gp.broadcast:
            broadcast = gp.broadcast[b]

            isinstance(broadcast.desc, basestring)
            assert broadcast.desc

            assert broadcast.desc in ['NFL Network', 'RedZone']


    @vcr.use_cassette('public_API/europe_broadcast.yaml')
    @staticmethod
    def test_name(gp):
        for b in gp.broadcast:
            broadcast = gp.broadcast[b]

            isinstance(broadcast.name, basestring)
            assert broadcast.name

            assert broadcast.name in ['nfl_network', 'redzone']


@pytest.mark.incremental
class TestBroadcastAuth(object):
    """These require authentication to Game Pass"""
    @vcr.use_cassette('public_API/europe_broadcast_auth_login.yaml')
    @staticmethod
    def test_login(gp):
        assert gp.login(pytest.gp_username, pytest.gp_password, force=True)


    #TODO: enable and record when it is broadcasting
    #@vcr.use_cassette('public_API/europe_broadcast_auth_redzone.yaml')
    #@staticmethod
    #def test_nfl_network(gp):
    #    rz = gp.broadcast['nfl_network']

    #    assert rz.on_air is True

    #    # make sure we have responses
    #    assert rz.streams

    #    # and check that there's actual links provided
    #    for f in ['hls', 'chromecast', 'connecttv']:
    #        assert rz.streams[f]
    #        assert 'https://' in rz.streams[f]


    @vcr.use_cassette('public_API/europe_broadcast_auth_redzone_nope.yaml')
    @staticmethod
    def test_on_air_redzone_nope(gp):
        rz = gp.broadcast['redzone']
        assert rz.on_air is False

        # make sure we don't have a response
        # TODO: what type. Empty or None?
        assert not rz.streams


    @vcr.use_cassette('public_API/europe_broadcast_auth_nfln.yaml')
    @staticmethod
    def test_nfl_network(gp):
        nfln = gp.broadcast['nfl_network']

        assert nfln.on_air is True

        # make sure we have responses
        assert nfln.streams

        # and check that there's actual links provided
        for f in ['hls', 'chromecast', 'connecttv']:
            assert nfln.streams[f]
            assert 'https://' in nfln.streams[f]


    # TODO: test for nfl network not being on air
