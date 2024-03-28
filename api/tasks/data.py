import logging
import json
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from ..serializer import GenerationAndCommitRequestSerializer
from .data_fetcher import DataFetcher

logger = logging.getLogger(__name__)

class GenerateDataView(APIView):
    def post(self, request):
        try:
            serializer = GenerationAndCommitRequestSerializer(data=request.data)
            if serializer.is_valid():
                data = serializer.validated_data
                task_id = data.get("task_id")
                generated_data = self.generate_data(data)
                return Response(generated_data, status=200)
            else:
                raise APIException(detail=serializer.errors, code=400)
        except Exception as e:
            detail = f"Failed to generate data: {str(e)}"
            logger.error(detail)
            raise APIException(detail=detail, code=500)

    def generate_data(self, data):
        task_id = data.get("task_id")
        req = data.get("req")
        openai_key = data.get("openai_key")
        redis = data.get("redis")

        try:
            fetcher = DataFetcher(req, openai_key, redis, task_id)
            generated_data = fetcher.fetch()
            self.save_data_to_redis(redis, task_id, generated_data)
            return {"data": generated_data}
        except Exception as e:
            detail = f"Failed to generate data: {str(e)}"
            self.save_error_to_redis(redis, task_id, detail)
            raise Exception(detail)

    def save_data_to_redis(self, redis, task_id, generated_data):
        logger.info("Saving data to Redis for task %s", task_id)
        data_to_save = generated_data[:req.num_samples] if req.num_samples else generated_data
        redis.hset(task_id, mapping={"status": "Generated", "Detail": json.dumps(data_to_save)})
        logger.info("Data saved to Redis for task %s", task_id)

    def save_error_to_redis(self, redis, task_id, detail):
        logger.error("Error occurred while generating data for task %s: %s", task_id, detail)
        redis.hset(task_id, mapping={"status": "Error", "Detail": detail})
