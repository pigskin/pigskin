import os
import pytest

from pigskin.pigskin import pigskin

@pytest.mark.vcr()
def test_get_team_games():
    gp = pigskin()

    games_int = gp.get_team_games(2018, '49ers')
    games_str = gp.get_team_games('2018', '49ers')

    for games in [games_int, games_str]:
        # make sure we have a response
        assert games

        # and that at least a tiny bit of the response is correct:
        assert games[2]['weekName'] == 'Preseason Week 3'


def test_get_team_games_failure():
    gp = pigskin()

    games = gp.get_team_games(2018, "never heard of 'em")

    # make sure we don't have results
    assert not games
