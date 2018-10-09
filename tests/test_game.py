from collections import OrderedDict
from datetime import datetime

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


def build_game_list(weeks=None, team=None):
    games_list = []

    for st in weeks:
        for w in weeks[st]:
            for g in weeks[st][w].games:
                games_list.append(weeks[st][w].games[g])

    for st in team.games:
        for g in team.games[st]:
            games_list.append(team.games[st][g])

    return games_list


@pytest.mark.incremental
class TestGame(object):
    """These don't require authentication to Game Pass."""
    @vcr.use_cassette('public_API/europe_game.yaml')
    @staticmethod
    def test_away_home(gp):
        weeks = gp.seasons['2017'].weeks
        team = gp.seasons['2017'].teams['Eagles']
        games = build_game_list(weeks=weeks, team=team)

        for game in games:
            assert game.home and game.away
            for team in [game.home, game.away]:
                assert type(team) is dict

                assert isinstance(team['name'], basestring)
                assert team['name']
                assert isinstance(team['city'], basestring)
                assert team['city']
                assert type(team['points']) is int
                # TODO: test that if the game is in the future, points should be None

                # TODO: should we validate the team name?


    @vcr.use_cassette('public_API/europe_game.yaml')
    @staticmethod
    def test_city(gp):
        weeks = gp.seasons['2017'].weeks
        team = gp.seasons['2017'].teams['Eagles']
        games = build_game_list(weeks=weeks, team=team)

        for game in games:
            isinstance(game.city, basestring)
            assert game.city

            # TODO: should we validate the city name?


    @vcr.use_cassette('public_API/europe_game.yaml')
    @staticmethod
    def test_phase(gp):
        weeks = gp.seasons['2017'].weeks
        team = gp.seasons['2017'].teams['Eagles']
        games = build_game_list(weeks=weeks, team=team)

        for game in games:
            isinstance(game.phase, basestring)
            assert game.phase

            # TODO: determine other phase names (live and future)
            assert game.phase in ['FINAL', 'FINAL_OVERTIME']


    @vcr.use_cassette('public_API/europe_game.yaml')
    @staticmethod
    def test_stadium(gp):
        weeks = gp.seasons['2017'].weeks
        team = gp.seasons['2017'].teams['Eagles']
        games = build_game_list(weeks=weeks, team=team)

        for game in games:
            isinstance(game.stadium, basestring)
            assert game.stadium

            # TODO: should we validate the stadium name?


    @vcr.use_cassette('public_API/europe_game.yaml')
    @staticmethod
    def test_start_time(gp):
        weeks = gp.seasons['2017'].weeks
        team = gp.seasons['2017'].teams['Eagles']
        games = build_game_list(weeks=weeks, team=team)

        for game in games:
            isinstance(game.start_time, basestring)
            assert game.start_time

            dt = gp.nfldate_to_datetime(game.start_time)
            assert type(dt) is datetime
            assert dt

            # TODO: should we verify that the date looks sane?


    @vcr.use_cassette('public_API/europe_game.yaml')
    @staticmethod
    def test_versions(gp):
        weeks = gp.seasons['2017'].weeks
        team = gp.seasons['2017'].teams['Eagles']
        games = build_game_list(weeks=weeks, team=team)

        for game in games:
            assert type(game.versions) is OrderedDict
            assert game.versions

            for v in game.versions:
                assert game.versions[v]
                # TODO: test that all are of type ``version``

                # make sure it's a known version type
                assert v in ['full', 'condensed', 'coach']

                # TODO: test order of OrderedDict


    # TODO: if data validation (city, stadium, etc) isn't done, then at least
    # one game should be selected and tested fully, for all content.
