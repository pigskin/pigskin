import pytest
import vcr
from collections import OrderedDict

from pigskin.pigskin import pigskin


try:  # Python 2.7
    # requests's ``json()`` function returns JSON strings as unicode (as per the
    # JSON spec). In 2.7, those are of type unicode rather than str. basestring
    # was created to help with that.
    # https://docs.python.org/2/library/functions.html#basestring
    basestring = basestring
except NameError:
    basestring = str


@pytest.fixture(scope='class')
def gp():
    with vcr.use_cassette('pigskin_gp.yaml'):
        return pigskin()


@pytest.mark.incremental
class TestPigskin(object):
    """These don't require authentication to Game Pass."""
    @vcr.use_cassette('pigskin_seasons.yaml')
    def test_seasons(self, gp):
        seasons = gp.seasons

        # make sure we have content and it's the right type
        assert seasons
        assert type(seasons) is OrderedDict

        prev = None
        for s in seasons:
            # TODO: assert type(seasons[s]) is season

            if prev:
                # make sure it's sorted high to low
                assert prev > s

            # make sure the years look sane-ish
            assert int(s) > 2000 and int(s) < 2050

            prev = s


    @vcr.use_cassette('pigskin_weeks.yaml')
    def test_weeks(self, gp):
        weeks = gp.seasons['2017'].weeks

        # make sure we have content and it's the right type
        assert weeks
        assert type(weeks) is OrderedDict

        # and all the season types are there
        assert weeks['pre']
        assert weeks['reg']
        assert weeks['post']
        assert type(weeks['pre']) is OrderedDict
        assert type(weeks['reg']) is OrderedDict
        assert type(weeks['post']) is OrderedDict

        # make sure it's in order
        i = 0
        for season_type in weeks:  # Python 2.7
            if i == 0:
                assert season_type == 'pre'
            elif i == 1:
                assert season_type == 'reg'
            elif i == 2:
                assert season_type == 'post'
            i += 1

        # TODO: test that all weeks are of type week

        # make sure the week numbers look sane
        for week in weeks['pre']:
            assert int(week) >= 0 and int(week) <= 4
        for week in weeks['reg']:
            assert int(week) >= 1 and int(week) <= 17
        for week in weeks['post']:
            assert int(week) >= 18 and int(week) <= 22

        # make sure at least some week descriptions look alright
        assert weeks['pre']['0'].desc == 'Hall of Fame'
        assert weeks['pre']['2'].desc == ''
        assert weeks['reg']['5'].desc == ''
        assert weeks['post']['22'].desc == 'Super Bowl'


    @vcr.use_cassette('pigskin_games.yaml')
    def test_games(self, gp):
        games = gp.seasons['2017'].weeks['reg']['8'].games

        # make sure we have content and it's the right type
        assert games
        assert type(games) is OrderedDict

        prev = None
        for g in games:
            game = games[g]
            # TODO: test that all values are of type game

            # check team data
            assert game.home and game.away
            for team in [game.home, game.away]:
                assert type(team) is dict

                assert team['name']
                assert isinstance(team['name'], basestring)
                assert team['city']
                assert isinstance(team['city'], basestring)
                assert type(team['points']) is int

            # check game data
            assert game.city
            assert isinstance(game.city, basestring)
            assert game.stadium
            assert isinstance(game.stadium, basestring)

            assert game.phase
            assert isinstance(game.phase, basestring)

            assert game.start_time
            assert isinstance(game.start_time, basestring)
            assert gp.nfldate_to_datetime(game.start_time)

            if prev:
                # make sure it's sorted low to high
                assert gp.nfldate_to_datetime(prev.start_time) <= gp.nfldate_to_datetime(game.start_time)

            #assert game.season
            #assert type(game.season) is str
            #assert game.season_type
            #assert type(game.season_type) is str
            #assert game.week
            #assert type(game.week) is str
            #assert game.week_desc
            #assert type(game.week_desc) is str

            prev = game


    # This cassette is unused, as ``versions`` does not cause any HTTP requests.
    # However, it remains here just in case that changes in the future.
    @vcr.use_cassette('pigskin_versions.yaml')
    def test_versions(self, gp):
        versions = gp.seasons['2017'].weeks['reg']['8'].games['Panthers@Buccaneers'].versions

        # make sure we have content and it's the right type
        assert versions
        assert type(versions) is OrderedDict

        for v in versions:
            assert versions[v]
            # TODO: test that all are of type ``version``

            # make sure it's a known version type
            assert v in ['full', 'condensed', 'coach']

            # make sure the description has content, si the right type, and is sane
            assert versions[v].desc
            assert isinstance(versions[v].desc, basestring)
            assert versions[v].desc in ['Full Game', 'Condensed Game', 'Coaches Tape']


    @vcr.use_cassette('pigskin_current.yaml')
    def test_current(self, gp):
        current = gp.current

        # make sure we have a response
        assert current
        assert type(current) is dict

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


    def test_nfldate_to_datetime(self, gp):
        # NOTE: nfldate_to_datetime() is also run for every game in test_games()
        nfldate = '2017-09-12T02:20:00.000Z'
        dt_utc = gp.nfldate_to_datetime(nfldate)

        assert dt_utc
        assert dt_utc.strftime('%Y.%m.%d-%H.%M.%S') == '2017.09.12-02.20.00'

        # localize it
        dt_local = gp.nfldate_to_datetime(nfldate, localize=True)
        assert dt_local
        # TODO: test localization in a way that still works on CI


    def test_nfldate_to_datetime_failure(self, gp):
        nfldate = 'not a date string'
        dt_utc = gp.nfldate_to_datetime(nfldate)

        assert not dt_utc

        dt_utc = gp.nfldate_to_datetime(nfldate, localize=True)
        assert not dt_utc


@pytest.mark.incremental
class TestPigskinAuth(object):
    """These require authentication to Game Pass"""
    @vcr.use_cassette('pigskin_login.yaml')
    def test_login(self, gp):
        assert gp.login(pytest.gp_username, pytest.gp_password, force=True)

        # make sure tokens are actually set
        assert gp._store.access_token
        assert gp._store.refresh_token


    @vcr.use_cassette('pigskin_check_for_subscription.yaml')
    def test_check_for_subscription(self, gp):
        assert gp.check_for_subscription()


    @vcr.use_cassette('pigskin_refresh_tokens.yaml')
    def test_refresh_tokens(self, gp):
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


    @vcr.use_cassette('pigskin_game_streams.yaml')
    def test_game_streams(self, gp):
        streams = gp.seasons['2017'].weeks['reg']['8'].games['Panthers@Buccaneers'].versions['full'].streams

        # make sure we have content and it's the right type
        assert streams
        assert type(streams) is dict

        for s in streams:
            assert streams[s]
            # TODO: test that all are of type ``stream``


@pytest.mark.incremental
class TestPigskinAuthFail(object):
    """These require authentication to Game Pass, and should fail without it."""
    @vcr.use_cassette('pigskin_login_failure.yaml')
    def test_login_failure(self, gp):
        assert not gp.login(username='I_do_not_exist', password='wrong', force=True)

        # make sure tokens are not set
        assert not gp._store.access_token
        assert not gp._store.refresh_token


    @vcr.use_cassette('pigskin_check_for_subscription_failure.yaml')
    def test_check_for_subscription(self, gp):
        assert not gp.check_for_subscription()


    @vcr.use_cassette('pigskin_refresh_tokens_failure.yaml')
    def test_refresh_tokens_no_login(self, gp):
        # refresh the tokens
        assert not gp.refresh_tokens()

        # make sure new tokens are not set
        assert not gp._store.access_token
        assert not gp._store.refresh_token
