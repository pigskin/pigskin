import pytest

from pigskin.pigskin import pigskin

@pytest.mark.vcr()
def test_refresh_tokens():
    gp = pigskin()

    # login
    assert gp.login(username=pytest.gp_username, password=pytest.gp_password)

    # make sure tokens are actually set
    assert gp.access_token
    assert gp.refresh_token

    # store the initial tokens
    first_access_token = gp.access_token
    first_refresh_token = gp.refresh_token

    # refresh the tokens
    assert gp.refresh_tokens()

    # make sure new tokens are actually set
    assert gp.access_token
    assert gp.refresh_token

    # and finally make sure they've actually been refreshed
    assert first_access_token != gp.access_token
    assert first_refresh_token != gp.refresh_token

@pytest.mark.vcr()
def test_refresh_tokens_no_login():
    gp = pigskin()

    # refresh the tokens
    assert not gp.refresh_tokens()

    # make sure new tokens are not set
    assert not gp.access_token
    assert not gp.refresh_token
