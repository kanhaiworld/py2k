import pytest

from py2k import NBA2KClient


@pytest.fixture
def client():
    return NBA2KClient(api_key="test-key")
