import pytest

from pigskin.pigskin import pigskin

@pytest.mark.vcr()
def test_get_game_versions():
    gp = pigskin()

    versions_int = gp.get_game_versions(2017090700, 2017)
    versions_str = gp.get_game_versions('2017090700', '2017')

    for versions in [versions_int, versions_str]:
        # make sure we have a response
        assert versions

        # and that at least the condensed video is there
        assert versions['Condensed game']


def test_get_game_versions_failure():
    gp = pigskin()

    versions = gp.get_game_versions('1919050399', '1919')

    # make sure we don't have results
    assert not versions
