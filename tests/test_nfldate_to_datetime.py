import pytest

from pigskin.pigskin import pigskin


@pytest.mark.vcr()
def test_nfldate_to_datetime():
    gp = pigskin()

    nfldate = '2017-09-12T02:20:00.000Z'
    dt_utc = gp.nfldate_to_datetime(nfldate)

    assert dt_utc
    assert dt_utc.strftime('%Y.%m.%d-%H.%M.%S') == '2017.09.12-02.20.00'

    # localize it
    dt_local = gp.nfldate_to_datetime(nfldate, localize=True)
    assert dt_local
    # TODO: test localization in a way that still works on CI


@pytest.mark.vcr()
def test_nfldate_to_datetime_failure():
    gp = pigskin()

    nfldate = 'not a date string'
    dt_utc = gp.nfldate_to_datetime(nfldate)

    assert not dt_utc

    dt_utc = gp.nfldate_to_datetime(nfldate, localize=True)
    assert not dt_utc
