import json
from api.models import GenerationAndCommitRequest
from api.tasks.data_fetcher import DataFetcher


def generate_data(redis, task_id, req_data, openai_key):
    if redis is None:
        raise Exception("Redis connection is not initialized")

    data = {"data": []}
    try:
        req = GenerationAndCommitRequest(**req_data)
        fetcher = DataFetcher(req, redis, task_id)
        d = fetcher.fetch()
        data["data"] = d
    except Exception as e:
        detail = f"Failed to generate data: {str(e)}"
        redis.hset(
            task_id, mapping={"status": "Error", "Progress": "None", "Detail": detail}
        )
        raise Exception(detail)

    data["data"] = data["data"][:req_data["num_samples"]]
    detail = {"data": data["data"] if len(data["data"]) < 50 else data["data"][:50]}
    redis.hset(
        task_id, mapping={"status": "Generated", "Detail": json.dumps(detail)}
    )
    return data
