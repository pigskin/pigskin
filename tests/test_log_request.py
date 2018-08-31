import pytest
import requests

from pigskin.pigskin import pigskin

gp = pigskin()

# These tests are just to make sure that the logging doesn't blow up. There's no
# need to test the output, just that it doesn't fail.

@pytest.mark.vcr()
def test_response_json():
    r = requests.get('https://httpbin.org/json')
    result = gp._log_request(r)
    assert result == True

@pytest.mark.vcr()
def test_response_html():
    r = requests.get('https://httpbin.org/html')
    result = gp._log_request(r)
    assert result == True

@pytest.mark.vcr()
def test_response_bytes():
    r = requests.get('https://httpbin.org/bytes/20')
    result = gp._log_request(r)
    assert result == True

def test_empty_handlel():
    result = gp._log_request(None)

    assert result == True
