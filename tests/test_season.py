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
class TestSeason(object):
    """These don't require authentication to Game Pass."""
    @vcr.use_cassette('public_API/europe_season.yaml')
    @staticmethod
    def test_weeks(gp):
        weeks = gp.seasons['2017'].weeks

        # make sure we have content and it's the right type
        assert type(weeks) is OrderedDict
        assert weeks

        # TODO: test that all weeks are of type week


    @vcr.use_cassette('public_API/europe_season_teams.yaml')
    @staticmethod
    def test_teams(gp):
        teams = gp.seasons['2017'].teams

        # make sure we have content and it's the right type
        assert type(teams) is OrderedDict
        assert teams

        # make sure we have all the teams
        assert len(teams) == 32

        # TODO: test that all teams are of type team


    @vcr.use_cassette('public_API/europe_season.yaml')
    @staticmethod
    def test_week_season_types(gp):
        weeks = gp.seasons['2017'].weeks

        # and all the season types are there
        assert type(weeks['pre']) is OrderedDict
        assert type(weeks['reg']) is OrderedDict
        assert type(weeks['post']) is OrderedDict
        assert weeks['pre']
        assert weeks['reg']
        assert weeks['post']

        # TODO: test that /only/ pre, reg, and post are present

        # make sure season types are in order
        i = 0
        for season_type in weeks:  # Python 2.7
            if i == 0:
                assert season_type == 'pre'
            elif i == 1:
                assert season_type == 'reg'
            elif i == 2:
                assert season_type == 'post'
            i += 1


    @vcr.use_cassette('public_API/europe_season.yaml')
    @staticmethod
    def test_week_numbers(gp):
        weeks = gp.seasons['2017'].weeks

        # make sure the week numbers look sane
        for week in weeks['pre']:
            assert int(week) >= 0 and int(week) <= 4
        for week in weeks['reg']:
            assert int(week) >= 1 and int(week) <= 17
        for week in weeks['post']:
            assert int(week) >= 18 and int(week) <= 22
