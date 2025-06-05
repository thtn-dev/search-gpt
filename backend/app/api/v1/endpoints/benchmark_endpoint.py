"""Endpoints for benchmarking JSON response performance."""

import random
import string

from fastapi import APIRouter
from fastapi.responses import ORJSONResponse


def generate_random_string(length: int = 10) -> str:
    """Generates a random string of a given length."""
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))


def create_sample_data(num_records: int = 1000) -> list[dict]:
    """Creates a list of sample data records."""
    data = []
    for i in range(num_records):
        record = {
            'id': i,
            'name': generate_random_string(15),
            'email': f'{generate_random_string(8)}@example.com',
            'age': random.randint(18, 65),
            'is_active': random.choice([True, False]),
            'address': {
                'street': f'{random.randint(1, 100)} {generate_random_string(10)} St',
                'city': generate_random_string(8),
                'zip_code': str(random.randint(10000, 99999)),
            },
            'tags': [generate_random_string(5) for _ in range(random.randint(1, 5))],
        }
        data.append(record)
    return data


constant_large_sample_data = create_sample_data(num_records=10)

router = APIRouter()


@router.get('/data-default')
async def get_data_default() -> list[dict]:
    """Returns sample data using the default FastAPI JSONResponse."""
    return constant_large_sample_data


@router.get('/data-orjson', response_class=ORJSONResponse)
async def get_data_orjson() -> list[dict]:
    """Returns sample data using ORJSONResponse for potentially faster serialization."""
    return constant_large_sample_data
