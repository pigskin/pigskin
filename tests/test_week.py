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
class TestWeek(object):
    """These don't require authentication to Game Pass."""
    @vcr.use_cassette('public_API/europe_week.yaml')
    @staticmethod
    def test_desc(gp):
        season = '2017'
        weeks = gp.seasons[season].weeks

        for st in weeks:
            assert st in ['pre', 'reg', 'post']

            for w in weeks[st]:
                week = weeks[st][w]
                isinstance(week.desc, basestring)

                if st == 'pre':
                    if w == '0':
                        # Hall of Fame has a description
                        assert week.desc
                    else:
                        assert not week.desc
                elif st == 'reg':
                    # no regular season games should have a description
                    assert not week.desc
                elif st == 'post':
                    # all post season games should have a description
                    assert week.desc

        # test the content of the descriptions
        if season != '2011':  # HoF was cancelled in 2011 due to the NFL lockout
            assert weeks['pre']['0'].desc == 'Hall of Fame'

        assert weeks['post']['18'].desc == 'Wild Card'
        assert weeks['post']['19'].desc == 'Divisional'
        assert weeks['post']['20'].desc == 'Conference'

        if int(season) >= 2009:
            assert weeks['post']['21'].desc == 'Pro Bowl'
            assert weeks['post']['22'].desc == 'Super Bowl'
        else:  # the Pro Bowl used to be after the Super Bowl
            assert weeks['post']['21'].desc == 'Super Bowl'
            assert weeks['post']['22'].desc == 'Pro Bowl'


    @staticmethod
    @vcr.use_cassette('public_API/europe_week_games.yaml')
    def test_games(gp):
        games = gp.seasons['2017'].weeks['reg']['8'].games

        # make sure we have content and it's the right type
        assert games
        assert type(games) is OrderedDict

        prev = None
        for g in games:
            game = games[g]
            if prev:
                # make sure it's sorted low to high
                dt_prev = gp.nfldate_to_datetime(prev.start_time)
                dt_game = gp.nfldate_to_datetime(game.start_time)
                assert dt_prev <= dt_game

            prev = game

        # TODO: test that all are of type game
