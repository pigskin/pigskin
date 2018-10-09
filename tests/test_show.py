from collections import OrderedDict
from datetime import datetime

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
class TestShow(object):
    """These don't require authentication to Game Pass."""
    @vcr.use_cassette('public_API/europe_show.yaml')
    @staticmethod
    def test_desc(gp):
        shows = gp.shows

        for s in shows:
            show = shows[s]

            isinstance(show.desc, basestring)
            # content is not required


    @vcr.use_cassette('public_API/europe_show.yaml')
    @staticmethod
    def test_logo(gp):
        shows = gp.shows

        for s in shows:
            show = shows[s]

            isinstance(show.logo, basestring)
            assert show.logo


    @vcr.use_cassette('public_API/europe_show.yaml')
    @staticmethod
    def test_name(gp):
        shows = gp.shows

        for s in shows:
            show = shows[s]

            isinstance(show.name, basestring)
            assert show.name


    @vcr.use_cassette('public_API/europe_show_seasons.yaml')
    @staticmethod
    def test_seasons(gp):
        shows = gp.shows

        for s in shows:
            show = shows[s]

            assert type(show.seasons) is OrderedDict
            assert show.seasons

            prev = 9999
            for s in show.seasons:
                season = show.seasons[s]

                # TODO: assert it has content
                # TODO: assert is type season

                # make sure the years look sane-ish
                assert int(s) > 2000 and int(s) < 2050

                # make sure it's sorted high to low
                assert int(prev) > int(s)
                prev = s
