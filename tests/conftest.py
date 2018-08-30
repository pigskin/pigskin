import os
import pytest

@pytest.fixture
def vcr_config():
    return {
        'decode_compressed_response': True
    }
