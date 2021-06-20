import pytest
from app import main
@pytest.fixture
def client():
    main.app.config['TESTING'] = True
    client = main.app.test_client()
    yield client