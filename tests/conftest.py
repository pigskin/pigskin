import os
import pytest
import json
import re
import socket
try:
    from urllib import quote  # Python 2.X
except ImportError:
    from urllib.parse import quote  # Python 3+

from pigskin.pigskin import pigskin


pytest.gp_username = os.getenv('PIGSKIN_USER', '')
pytest.gp_password = os.getenv('PIGSKIN_PASS', '')
scrub_list = []

for i in [ pytest.gp_username, pytest.gp_password ]:
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

def scrub_secrets(text):
    for i in scrub_list:
        text = text.replace(i, 'REDACTED')

    return text

def scrub_request(request):
    try:
        body = request.body.decode()
    except (AttributeError, UnicodeDecodeError) as e:
        return request

    body = scrub_secrets(body)
    request.body = body.encode()

    return request

def scrub_response(response):
    try:
        body = response['body']['string'].decode()
    except (AttributeError, UnicodeDecodeError) as e:
        return response

    body = scrub_secrets(body)
    body = scrub_IPs(body)
    response['body']['string'] = body.encode()

    try:  # load JSON as a python dict so it can be pretty printed
        parsed = json.loads(body)
        response['body']['pretty'] = parsed
    except ValueError as e:
        pass

    return response

@pytest.fixture
def vcr_config():
    return {
        'decode_compressed_response': True,
        'before_record_request': scrub_request,
        'before_record_response': scrub_response,
    }
