import pytest

from pigskin.pigskin import pigskin

@pytest.mark.vcr()
def test_login_success():
    gp = pigskin()
    result = gp.login(username=pytest.gp_username, password=pytest.gp_password)
    assert result == True

@pytest.mark.vcr()
def test_login_failure():
    gp = pigskin()
    result = gp.login(username='I_do_not_exist', password='wrong')
    assert result == False
