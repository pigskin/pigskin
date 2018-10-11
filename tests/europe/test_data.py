import pytest
import vcr

from pigskin.pigskin import pigskin


@pytest.fixture(scope='class')
def gp():
    with vcr.use_cassette('backends/europe/gp.yaml'):
        return pigskin()


@pytest.mark.incremental
class TestEuropeData(object):
    """These don't require authentication to Game Pass."""
    @vcr.use_cassette('backends/europe/data__team_seo_name.yaml')
    @staticmethod
    def test__team_seo_name(gp):
        season = gp.current['season']
        teams = gp.seasons[season].teams

        # I don't want to rely on the gp.season[current_season].teams behavior
        # remaining unchanged. Thus I am testing this process explicitly.
        for t in teams:
            # test it directly (though will be left unused)
            seo_name = gp._data._team_seo_name(t)
            assert seo_name

            # _get_team_games_easy() is the only consumer of this. Without the
            # correct seo_name, it can't get the games.
            games = gp._data._get_team_games_easy(t, season)
            assert games['reg']
            assert len(games['reg']) == 16
