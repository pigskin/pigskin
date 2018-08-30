import os
import pytest
import json
try:
    from urllib import quote  # Python 2.X
except ImportError:
    from urllib.parse import quote  # Python 3+

from pigskin.pigskin import pigskin


pytest.gp_username = os.getenv('PIGSKIN_USER', '')
pytest.gp_password = os.getenv('PIGSKIN_PASS', '')

scrub_list = [
    pytest.gp_username,
    pytest.gp_password,
    quote(pytest.gp_username),
    quote(pytest.gp_password)
]

def scrub_request(request):
    for i in scrub_list:
        request.body = request.body.decode().replace(i, 'REDACTED').encode()
    return request

def scrub_response(response):
    body = response['body']['string'].decode()
    for i in scrub_list:
        body = body.replace(i, 'REDACTED')

    try:
        parsed = json.loads(body)
        response['body']['string'] = parsed
    except JSONDecodeError as e:
        response['body']['string'] = body.encode()

    return response

@pytest.fixture
def vcr_config():
    return {
        'decode_compressed_response': True,
        'before_record_request': scrub_request,
        'before_record_response': scrub_response,
    }
