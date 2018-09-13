import pytest

from pigskin.pigskin import pigskin

@pytest.mark.vcr()
def test_seasons():
    gp = pigskin()

    # make sure it's a list
    assert type(gp.seasons) is list

    # make sure we have content
    assert gp.seasons

    # make sure it's sorted high to low
    assert gp.seasons == sorted(gp.seasons, reverse=True)

    # make sure the seasons look sane-ish
    for i in gp.seasons:
        assert int(i) > 2000 and int(i) < 2050
