import logging
import json
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from .data_fetcher import DataFetcher
from ..serializer import GenerationAndCommitRequestSerializer
logger = logging.getLogger(__name__)

class GenerateDataView(APIView):
    def post(self, request):
        try:
            serializer = GenerationAndCommitRequestSerializer(data=request.data)
            if serializer.is_valid():
                data = serializer.validated_data
                task_id = data.get("task_id")
                result = self.generate_data(data)
                return Response(result, status=200)
            else:
                raise APIException(detail=serializer.errors, code=400)
        except Exception as e:
            detail = f"Failed to generate data: {str(e)}"
            logger.error(detail)
            raise APIException(detail=detail, code=500)
    def generate_data(self, data):
        redis = data.get("redis")
        task_id = data.get("task_id")
        req = data.get("req")
        openai_key = data.get("openai_key")

        data = {"data": []}
        try:
            fetcher = DataFetcher(req, openai_key, redis, task_id)
            d = fetcher.fetch()
            data["data"] = d
        except Exception as e:
            detail = f"Failed to generate data: {str(e)}"
            redis.hset(
                task_id, mapping={"status": "Error", "Progress": "None", "Detail": detail}
            )
            raise Exception(detail)
        logger.info("Generated %s samples", len(data["data"]))
        logger.info("Saving data to redis")
        data["data"] = data["data"][: req.num_samples]
        detail = {}
        detail["data"] = data["data"] if len(data["data"]) < 50 else data["data"][:50]
        redis.hset(
            task_id, mapping={"status": "Generated", "Detail": json.dumps(detail)}
        )
        logger.info("Task %s completed", task_id)
        return data
