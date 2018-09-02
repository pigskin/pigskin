import os
import pytest

from pigskin.pigskin import pigskin

@pytest.mark.vcr()
def test_get_games():
    gp = pigskin()

    games_int = gp.get_games(2017, 'reg', 8)
    games_str = gp.get_games('2017', 'reg', '8')

    for games in [games_int, games_str]:
        # make sure we have a response
        assert games

        # and that at least a tiny bit of the response is correct:
        assert games[0]['video']['title'] == 'Miami Dolphins @ Baltimore Ravens'
