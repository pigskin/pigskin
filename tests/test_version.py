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
class TestVersion(object):
    """These don't require authentication to Game Pass."""
    @vcr.use_cassette('public_API/europe_version.yaml')
    @staticmethod
    def test_desc(gp):
        weeks = gp.seasons['2017'].weeks
        team = gp.seasons['2017'].teams['Packers']
        games = build_game_list(weeks=weeks, team=team)

        for game in games:
            for v in game.versions:
                version = game.versions[v]

                isinstance(version.desc, basestring)
                assert version.desc

                assert version.desc in ['Full Game', 'Condensed Game', 'Coaches Tape']


@pytest.mark.incremental
class TestVersionAuth(object):
    """These require authentication to Game Pass"""
    @vcr.use_cassette('public_API/europe_version_auth.yaml')
    @staticmethod
    def test_login(gp):
        assert gp.login(pytest.gp_username, pytest.gp_password, force=True)


    @vcr.use_cassette('public_API/europe_version_auth_streams.yaml')
    @staticmethod
    def test_streams(gp):
        # TODO: test a variety of games; but looping over all of them (as above)
        # would cause an epic storm of requests. Perhaps 10 selected games.
        versions = gp.seasons['2017'].weeks['reg']['8'].games['Panthers@Buccaneers'].versions

        for v in versions:
            version = versions[v]

            # make sure we have content and it's the right type
            assert type(version.streams) is dict
            assert version.streams

            for s in version.streams:
                assert version.streams[s]
                # TODO: test that they are of type ``stream``
