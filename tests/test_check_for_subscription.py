import pytest

from pigskin.pigskin import pigskin

@pytest.mark.vcr()
def test_check_for_subscription():
    gp = pigskin()

    # login
    assert gp.login(pytest.gp_username, pytest.gp_password, force=True)

    assert gp.check_for_subscription()
