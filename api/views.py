from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json
import requests

from api.hr_repo import push_dataset_to_hf

logger = logging.getLogger(__name__)
from api.utils import DataFetcher

@api_view(['POST'])
def generate_data(request):
    if request.method == 'POST':
        req_data = json.loads(request.body)
        task_id = req_data['task_id']
        openai_key = req_data['openai_key']
        redis = req_data['redis']
        req = req_data['request']

        data = {"data": []}
        try:
            fetcher = DataFetcher(req, openai_key, redis, task_id)
            d = fetcher.fetch().result()
            data["data"] = d
        except Exception as e:
            detail = f"Failed to generate data: {str(e)}"
            redis.hset(
                task_id, mapping={"status": "Error", "Progress": "None", "Detail": detail}
            )
            return Response(detail, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.info("Generated %s samples", len(data["data"]))
        logger.info("Saving data to redis")
        data["data"] = data["data"][: req.num_samples]
        detail = {}
        detail["data"] = data["data"] if len(data["data"]) < 50 else data["data"][:50]
        redis.hset(
            task_id, mapping={"status": "Generated", "Detail": json.dumps(detail)}
        )
        logger.info("Task %s completed", task_id)

        return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
def generate_and_push_data(request):
    if request.method == 'POST':
        req_data = json.loads(request.body)
        task_id = req_data['task_id']
        openai_key = req_data['openai_key']
        redis = req_data['redis']
        req = req_data['request']
        huggingface_key = req_data['huggingface_key']

        data = generate_data(redis, task_id, req, openai_key)
        redis.hset(
            task_id,
            mapping={
                "status": "Completed",
                "Progress": "None",
                "Detail": json.dumps(data),
            },
        )
        push_dataset_to_hf(redis, task_id, req, huggingface_key, data)

        return Response(data, status=status.HTTP_200_OK)
