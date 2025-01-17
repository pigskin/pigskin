import os
import pytest
import json
import re
import socket
import vcr
from hashlib import sha256
from pigskin.pigskin import pigskin
try:
    from urllib.parse import quote
except ImportError:  # Python 2.7
    from urllib import quote


@pytest.fixture(scope='class')
def gp():
    with vcr.use_cassette('public_API/europe_gp.yaml'):
        return pigskin()

pytest.gp_username = os.getenv('PIGSKIN_USER', '')
pytest.gp_password = os.getenv('PIGSKIN_PASS', '')
scrub_list = []
token_list = {}

for i in [pytest.gp_username, pytest.gp_password]:
    if i:
        scrub_list.append(i)
        scrub_list.append(quote(i))


def scrub_IPs(text):
    # TODO: also redact IPv6 IPs. When we drop Python 2.7 and < 3.4, we can use
    # ``ipaddress`` to validate both IPv4 and IPv6 IPs
    ips = re.findall(r"\d{1,3}(?:\.\d{1,3}){3}", text)

    for addr in ips:
        try:
            socket.inet_aton(addr)
        except socket.error:  # invalid IP
            continue

        text = text.replace(addr, 'REDACTED')

    return text


def search_for_tokens(text):
    """Add any tokens to a list to scrub and generate fake versions of it.
    The fake keys are generated so that refresh_tokens() can test that indeed
    the tokens /did/ change without leaking these tokens."""
    try:
        parsed = json.loads(text)
    except ValueError:
        return

    for t in ['access_token', 'refresh_token']:
        try:
            if parsed[t] not in token_list:
                fake_token = sha256(parsed[t].encode()).hexdigest()
                token_list[parsed[t]] = 'FAKE_TOKEN_' + fake_token
        except (KeyError, TypeError):
            continue


def scrub_profile_info(text):
    """Gigya auth and the account pages contain personal info. Scrub it."""
    try:
        parsed = json.loads(text)
    except ValueError:
        return text

    for i in ['profile', 'billing']:
        try:
            if parsed[i]:
                parsed[i] = 'REDACTED'
        except (KeyError, TypeError):
            pass

    text = json.dumps(parsed)
    return text


def scrub_secrets(text):
    search_for_tokens(text)

    for i in scrub_list:
        text = text.replace(i, 'REDACTED')

    for k in token_list:
        text = text.replace(k, token_list[k])

    text = scrub_IPs(text)
    text = scrub_profile_info(text)

    return text


def scrub_request(request):
    # scrub body
    try:
        body = request.body.decode()
    except (AttributeError, UnicodeDecodeError):  # likely binary data
        return request
    else:
        body = scrub_secrets(body)
        request.body = body.encode()

    return request


def scrub_response(response):
    try:
        body = response['body']['string'].decode()
    except (AttributeError, UnicodeDecodeError):  # likely binary data
        return response

    body = scrub_secrets(body)
    response['body']['string'] = body.encode()

    try:  # load JSON as a python dict so it can be pretty printed
        parsed = json.loads(body)
        response['body']['pretty'] = parsed
    except ValueError:
        pass

    return response


record_mode = 'once'
if os.environ.get('CI') == 'true':
    record_mode = 'none'

vcr.default_vcr = vcr.VCR(
    cassette_library_dir='tests/cassettes',
    record_mode=record_mode,
    decode_compressed_response=True,
    before_record_request=scrub_request,
    before_record_response=scrub_response,
    filter_headers=[('Authorization', 'REDACTED')],
)
vcr.use_cassette = vcr.default_vcr.use_cassette
