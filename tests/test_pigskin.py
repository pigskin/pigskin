from collections import OrderedDict

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
        assert seasons
        assert type(seasons) is OrderedDict

        assert len(seasons) > 0
        prev = 9999
        for s in seasons:
            # TODO: assert type(seasons[s]) is season

            # make sure the years look sane-ish
            assert int(s) > 2000 and int(s) < 2050

            # make sure it's sorted high to low
            assert int(prev) > int(s)
            prev = s


    @vcr.use_cassette('public_API/europe_pigskin_teams.yaml')
    @staticmethod
    def test_teams(gp):
        # we test 2015 for the St. Louis Rams; 2017 because week 1 had only 15
        # games, and 2018 because it should be normal/typical.
        for season in ['2015', '2017', '2018']:
            teams = gp.seasons[season].teams

            # teams move; make sure the Rams' info is correct
            if season == '2015':
                assert teams['Rams'].city == 'St. Louis'
                assert teams['Rams'].abbr == 'STL'
            else:
                assert teams['Rams'].city == 'Los Angeles'
                assert teams['Rams'].abbr == 'LA'

            # The keys and names should always match
            for t in teams:
                assert t == teams[t].name
                # TODO: check that they are alphabetized
                # TODO: test that all teams are of type team

            # make the games list is there and is of the right type
            assert teams['Eagles'].games
            assert type(teams['Eagles'].games) is OrderedDict

            # check some other random info
            assert teams['Packers'].city == 'Green Bay'
            assert teams['Eagles'].abbr == 'PHI'
            assert teams['Jets'].abbr == 'NYJ'

        # test games for a team
        teams = gp.seasons['2017'].teams

        for season_type in teams['Eagles'].games:
            # a known season type
            assert season_type in ['pre', 'reg', 'post']
            assert type(teams['Eagles'].games[season_type]) is OrderedDict

            for game_name in teams['Eagles'].games[season_type]:
                assert 'Eagles' in game_name
                # TODO: check that the games are sorted in order
                # TODO: test that they are of type game

        # test post season (Eagles won the Super Bowl in 2017)
        assert teams['Eagles'].games['post']['Eagles@Patriots']

        # there should be no post season entry for teams that miss out
        assert 'post' not in teams['Browns'].games

        # TODO: these game tests may really just belong elsewhere. it's a bit
        # complicated with the weeks.games and team.games


    @vcr.use_cassette('public_API/europe_pigskin_weeks.yaml')
    @staticmethod
    def test_weeks(gp):
        weeks = gp.seasons['2017'].weeks
        # make sure at least some week descriptions look alright
        assert weeks['pre']['0'].desc == 'Hall of Fame'
        assert weeks['pre']['2'].desc == ''
        assert weeks['reg']['5'].desc == ''
        assert weeks['post']['22'].desc == 'Super Bowl'


    @vcr.use_cassette('public_API/europe_pigskin_games.yaml')
    @staticmethod
    def test_games(gp):
        games = gp.seasons['2017'].weeks['reg']['8'].games
        # TODO: create a list for team_games by walking
        #       gp.seasons['2018'].teams['Steelers'].weeks[*][*]

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
                # TODO: test that if the game is in the future, points should be None

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

        # TODO: test a specific game, fully, for all content.


    # This cassette is unused, as ``versions`` does not cause any HTTP requests.
    # However, it remains here just in case that changes in the future.
    @vcr.use_cassette('public_API/europe_pigskin_versions.yaml')
    @staticmethod
    def test_versions(gp):
        versions = gp.seasons['2017'].weeks['reg']['8'].games['Panthers@Buccaneers'].versions
        # TODO: test gp.seasons['2017'].teams['Steelers'].weeks['reg']['8'].versions

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


    @vcr.use_cassette('public_API/europe_pigskin_shows.yaml')
    @staticmethod
    def test_shows(gp):
        shows = gp.shows

        # make sure we have content and it's the right type
        assert shows
        assert type(shows) is OrderedDict

        for name in shows:
            assert isinstance(shows[name].desc, basestring)

            assert isinstance(shows[name].name, basestring)

            assert shows[name].name
            assert isinstance(shows[name].name, basestring)
            assert name == shows[name].name

            assert type(shows[name].seasons) is OrderedDict
            assert len(shows[name].seasons) > 0

            prev = 9999
            for s in shows[name].seasons:
                # TODO: assert is type season

                # make sure the years look sane-ish
                assert int(s) > 2000 and int(s) < 2050

                # make sure it's sorted high to low
                assert int(prev) > int(s)
                prev = s


    @vcr.use_cassette('public_API/europe_pigskin_current.yaml')
    @staticmethod
    def test_current(gp):
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


    @staticmethod
    def test_nfldate_to_datetime(gp):
        # NOTE: nfldate_to_datetime() is also run for every game in test_games()
        nfldate = '2017-09-12T02:20:00.000Z'
        dt_utc = gp.nfldate_to_datetime(nfldate)

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


    @vcr.use_cassette('public_API/europe_pigskin_auth_game_streams.yaml')
    @staticmethod
    def test_game_streams(gp):
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
