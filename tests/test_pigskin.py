from collections import OrderedDict
from datetime import datetime

import pytest
import vcr
from pigskin.pigskin import pigskin


try:  # Python 2.7
    # requests's ``json()`` function returns strings as unicode (as per the
    # JSON spec). In 2.7, those are of type unicode rather than str. basestring
    # was created to help with that.
    # https://docs.python.org/2/library/functions.html#basestring
    basestring = basestring
except NameError:
    basestring = str


@pytest.mark.incremental
class TestPigskin(object):
    """These don't require authentication to Game Pass."""
    @vcr.use_cassette('public_API/europe_pigskin_seasons.yaml')
    @staticmethod
    def test_seasons(gp):
        seasons = gp.seasons

        # make sure we have content and it's the right type
        assert type(seasons) is OrderedDict
        assert seasons

        assert len(seasons) > 0
        prev = 9999
        for s in seasons:
            # TODO: assert type(seasons[s]) is season
            assert seasons[s]

            # make sure the years look sane-ish
            assert int(s) > 2000 and int(s) < 2050

            # make sure it's sorted high to low
            assert int(prev) > int(s)
            prev = s


    @staticmethod
    @vcr.use_cassette('public_API/europe_pigskin_teams.yaml')
    def test_teams(gp):
        teams = gp.seasons['2017'].teams

        # make sure we have content and it's the right type
        assert type(teams) is OrderedDict
        assert teams

        # TODO: check that they are alphabetized
        # TODO: test that all teams are of type team


    @vcr.use_cassette('public_API/europe_pigskin_shows.yaml')
    @staticmethod
    def test_shows(gp):
        shows = gp.shows

        # make sure we have content and it's the right type
        assert type(shows) is OrderedDict
        assert shows

        for name in shows:
            assert name == shows[name].name


    @vcr.use_cassette('public_API/europe_pigskin_current.yaml')
    @staticmethod
    def test_current(gp):
        current = gp.current

        # make sure we have a response
        assert type(current) is dict
        assert current

        # that the fields are there and set
        assert current['season']
        assert current['season_type']
        assert current['week']
        assert isinstance(current['season'], basestring)
        assert isinstance(current['season_type'], basestring)
        assert isinstance(current['week'], basestring)

        # and that the data format remains stable and sane-ish
        assert int(current['season']) > 2000 and int(current['season']) < 2050
        assert current['season_type'] in ['pre', 'reg', 'post']
        assert int(current['week']) > 0 and int(current['week']) < 23

        if current['season_type'] == 'pre':
            assert int(current['week']) >= 0 and int(current['week']) <= 4
        if current['season_type'] == 'reg':
            assert int(current['week']) >= 1 and int(current['week']) <= 17
        if current['season_type'] == 'post':
            assert int(current['week']) >= 18 and int(current['week']) <= 22


    @staticmethod
    def test_nfldate_to_datetime(gp):
        # NOTE: nfldate_to_datetime() is also run for every game in test_games()
        nfldate = '2017-09-12T02:20:00.000Z'
        dt_utc = gp.nfldate_to_datetime(nfldate)

        assert type(dt_utc) is datetime
        assert dt_utc
        assert dt_utc.strftime('%Y.%m.%d-%H.%M.%S') == '2017.09.12-02.20.00'

        # localize it
        dt_local = gp.nfldate_to_datetime(nfldate, localize=True)
        assert dt_local
        # TODO: test localization in a way that still works on CI


    @staticmethod
    def test_nfldate_to_datetime_failure(gp):
        nfldate = 'not a date string'
        dt_utc = gp.nfldate_to_datetime(nfldate)

        assert not dt_utc

        dt_utc = gp.nfldate_to_datetime(nfldate, localize=True)
        assert not dt_utc


@pytest.mark.incremental
class TestPigskinAuth(object):
    """These require authentication to Game Pass"""
    @vcr.use_cassette('public_API/europe_pigskin_auth_login.yaml')
    @staticmethod
    def test_login(gp):
        assert gp.login(pytest.gp_username, pytest.gp_password, force=True)

        # make sure tokens are actually set
        assert gp._store.access_token
        assert gp._store.refresh_token


    @vcr.use_cassette('public_API/europe_pigskin_auth_subscription.yaml')
    @staticmethod
    def test_subscription(gp):
        assert gp.subscription
        isinstance(gp.subscription, basestring)


    @vcr.use_cassette('public_API/europe_pigskin_auth_refresh_tokens.yaml')
    @staticmethod
    def test_refresh_tokens(gp):
        # store the initial tokens
        first_access_token = gp._store.access_token
        first_refresh_token = gp._store.refresh_token

        # refresh the tokens
        assert gp.refresh_tokens()

        # make sure new tokens are actually set
        assert gp._store.access_token
        assert gp._store.refresh_token

        # and finally make sure they've actually been refreshed
        assert first_access_token != gp._store.access_token
        assert first_refresh_token != gp._store.refresh_token


@pytest.mark.incremental
class TestPigskinAuthFail(object):
    """These require authentication to Game Pass, and should fail without it."""
    @vcr.use_cassette('public_API/europe_pigskin_bad_auth_login.yaml')
    @staticmethod
    def test_bad_auth_login(gp):
        assert not gp.login(username='I_do_not_exist', password='wrong', force=True)

        # make sure tokens are not set
        assert not gp._store.access_token
        assert not gp._store.refresh_token


    @vcr.use_cassette('public_API/europe_pigskin_bad_auth_subscription.yaml')
    @staticmethod
    def test_bad_auth_subscription(gp):
        assert gp.subscription is None


    @vcr.use_cassette('public_API/europe_pigskin_bad_auth_refresh_tokens.yaml')
    @staticmethod
    def test_bad_auth_refresh_tokens(gp):
        # refresh the tokens
        assert not gp.refresh_tokens()

        # make sure new tokens are not set
        assert not gp._store.access_token
        assert not gp._store.refresh_token
