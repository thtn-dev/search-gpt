import random
import string
from fastapi.responses import JSONResponse, ORJSONResponse
from fastapi import APIRouter

def generate_random_string(length=10):
    return ''.join(random.choice(string.ascii_letters) for i in range(length))

def create_sample_data(num_records=1000):
    data = []
    for i in range(num_records):
        record = {
            "id": i,
            "name": generate_random_string(15),
            "email": f"{generate_random_string(8)}@example.com",
            "age": random.randint(18, 65),
            "is_active": random.choice([True, False]),
            "address": {
                "street": f"{random.randint(1, 100)} {generate_random_string(10)} St",
                "city": generate_random_string(8),
                "zip_code": str(random.randint(10000, 99999))
            },
            "tags": [generate_random_string(5) for _ in range(random.randint(1, 5))]
        }
        data.append(record)
    return data

constant_large_sample_data = create_sample_data(num_records=10)

router = APIRouter()
@router.get("/data-default")
async def get_data_default():
    return constant_large_sample_data

@router.get("/data-orjson", response_class=ORJSONResponse)
async def get_data_orjson():
    return constant_large_sample_data