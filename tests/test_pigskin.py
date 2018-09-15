import pytest
import vcr
from collections import OrderedDict

from pigskin.pigskin import pigskin


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

        # make sure it's sorted high to low
        prev = None
        for i in seasons:
            if prev:
                assert prev > i
            prev = i

        for i in seasons:
            # make sure the years look sane-ish
            assert int(i) > 2000 and int(i) < 2050
            # TODO: assert type(i) is season

        # TODO: test that all values are of type season


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
        for season_type in weeks:
            if i == 0:
                assert season_type == 'pre'
            elif i == 1:
                assert season_type == 'reg'
            elif i == 2:
                assert season_type == 'post'
            i += 1

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

        # TODO: test that all values are of type week


    @vcr.use_cassette('pigskin_games.yaml')
    def test_games(self, gp):
        games = gp.seasons['2017'].weeks['reg']['8'].games

        # make sure we have content and it's the right type
        assert games
        assert type(games) is list

        # and that at least a tiny bit of the response is correct:
        assert games[0]['video']['title'] == 'Miami Dolphins @ Baltimore Ravens'

        # TODO: test that all values are of type game


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
