from collections import OrderedDict

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
class TestTeam(object):
    """These don't require authentication to Game Pass."""
    @vcr.use_cassette('public_API/europe_team.yaml')
    @staticmethod
    def test_abbr(gp):
        # testing multiple years to prime the cassette cache for other tests
        for season in ['2016', '2017']:
            teams = gp.seasons[season].teams

            # The keys and names should always match
            for t in teams:
                team = teams[t]

                isinstance(team.abbr, basestring)
                assert team.abbr

                # abbreviations are 2-3 characters long
                assert len(team.abbr) == 2 or len(team.abbr) == 3

                # TODO: should we go so far as to validate the data?


    @vcr.use_cassette('public_API/europe_team.yaml')
    @staticmethod
    def test_city(gp):
        season = '2017'
        teams = gp.seasons[season].teams

        # The keys and names should always match
        for t in teams:
            team = teams[t]

            isinstance(team.city, basestring)
            assert team.city

            # the key and the team name should be the same
            assert t == team.name

            # TODO: should we go so far as to validate the data?


    @staticmethod
    @vcr.use_cassette('public_API/europe_team_games.yaml')
    def test_games(gp):
        # This test doesn't loop over all teams because it'll require 1 HTTP
        # request per week per team for non-current seasons. Instead, just
        # spot-check.
        teams = gp.seasons['2017'].teams

        # make sure we have content and it's the right type
        assert teams['Eagles'].games
        assert type(teams['Eagles'].games) is OrderedDict

        for season_type in teams['Eagles'].games:
            assert season_type in ['pre', 'reg', 'post']

            assert type(teams['Eagles'].games[season_type]) is OrderedDict
            for game_name in teams['Eagles'].games[season_type]:
                assert 'Eagles' in game_name

        # test post season (Eagles won the Super Bowl in 2017)
        assert teams['Eagles'].games['post']['Eagles@Patriots']

        # there should be no post season entry for teams that miss out
        assert 'post' not in teams['Browns'].games


    #@vcr.use_cassette('public_API/europe_team.yaml')
    #@staticmethod
    #def test_logo(gp):
    #    season = '2017'
    #    teams = gp.seasons[season].teams

    #    # The keys and names should always match
    #    for t in teams:
    #        team = teams[t]

    #        isinstance(team.logo, basestring)
    #        assert team.logo
    #        assert is_url(team.logo)


    @vcr.use_cassette('public_API/europe_team.yaml')
    @staticmethod
    def test_name(gp):
        season = '2017'
        teams = gp.seasons[season].teams

        # The keys and names should always match
        for t in teams:
            team = teams[t]

            isinstance(team.name, basestring)
            assert team.name

            # the key and the team name should be the same
            assert t == team.name

            # TODO: should we go so far as to validate the data?


    @vcr.use_cassette('public_API/europe_team.yaml')
    @staticmethod
    def test_moving_team(gp):
        for season in ['2016', '2017']:
            teams = gp.seasons[season].teams

            # the Rams playes in St. Louis 1995->2016 and LA the rest
            if int(season) >= 2016 or int(season) <= 1994:
                assert teams['Rams'].city == 'Los Angeles'
                assert teams['Rams'].abbr == 'LA'
            else:
                assert teams['Rams'].city == 'St. Louis'
                assert teams['Rams'].abbr == 'STL'
