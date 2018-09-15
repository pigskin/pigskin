import pytest
import vcr
from collections import OrderedDict

from pigskin.pigskin import pigskin

@pytest.fixture(scope='class')
def gp():
    with vcr.use_cassette('pigskin_gp.yaml'):
        return pigskin()


#@pytest.mark.usefixtures('gp')
@pytest.mark.incremental
class TestPigskin(object):
    """These tests don't require authentication to the service"""
    @pytest.fixture(autouse=True)
    def start(self, gp):
        gp.__module__


    @vcr.use_cassette('pigskin_seasons.yaml')
    def test_seasons(self, gp):
        seasons = gp.seasons

        # make sure we have content and it's the right type
        assert seasons is not None
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


    @vcr.use_cassette('pigskin_weeks.yaml')
    def test_weeks(self, gp):
        weeks = gp.seasons['2017'].weeks

        # make sure we have content and it's the right type
        assert weeks is not None
        assert type(weeks) is OrderedDict

        # and all the season types are there
        assert weeks['pre']
        assert weeks['reg']
        assert weeks['post']

        # make sure the week numbers look sane
        for week in weeks['pre']:
            assert int(week) >= 0 and int(week) <= 4
        for week in weeks['reg']:
            assert int(week) >= 1 and int(week) <= 17
        for week in weeks['post']:
            assert int(week) >= 18 and int(week) <= 22


    @vcr.use_cassette('pigskin_games.yaml')
    def test_games(self, gp):
        games = gp.seasons['2017'].weeks['reg']['8'].games

        # make sure we have content and it's the right type
        assert games is not None
        assert type(games) is list

        # and that at least a tiny bit of the response is correct:
        assert games[0]['video']['title'] == 'Miami Dolphins @ Baltimore Ravens'
