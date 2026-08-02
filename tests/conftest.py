import pytest


@pytest.fixture
def dob():
    from datetime import date

    return date(1990, 1, 15)
