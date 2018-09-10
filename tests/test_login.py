import pytest

from pigskin.pigskin import pigskin

@pytest.mark.vcr()
def test_login():
    gp = pigskin()
    assert gp.login(pytest.gp_username, pytest.gp_password, force=True)


@pytest.mark.vcr()
def test_login_failure():
    gp = pigskin()
    assert not gp.login(username='I_do_not_exist', password='wrong', force=True)
