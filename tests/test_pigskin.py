import pytest
from collections import OrderedDict

from pigskin.pigskin import pigskin

@pytest.mark.vcr()
def test_pigskin_seasons():
    gp = pigskin()

    # make sure it's a list
    assert type(gp.seasons) is OrderedDict

    # make sure we have content
    assert gp.seasons is not None

    # make sure it's sorted high to low
    prev = None
    for i in gp.seasons:
        if prev:
            assert prev > i
        prev = i

    # make sure the seasons look sane-ish
    for i in gp.seasons:
        assert int(i) > 2000 and int(i) < 2050
