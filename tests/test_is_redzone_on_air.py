import pytest

from pigskin.pigskin import pigskin

#TODO: enable and record when it is on air.
#@pytest.mark.vcr()
#def test_is_redzone_on_air_yes():
#    gp = pigskin()
#
#    assert gp.is_redzone_on_air()

@pytest.mark.vcr()
def test_is_redzone_on_air_nope():
    gp = pigskin()

    assert gp.is_redzone_on_air() == False
