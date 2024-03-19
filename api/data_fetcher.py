import json
import logging
import requests
from django.core.cache import cache
from rest_framework.exceptions import APIException

from . import utils

logger = logging.getLogger(__name__)

class HFException(APIException):
    pass

class DataFetcher:
    MAX_CONCURRENT_FETCHES = 10

    def __init__(
        self,
        openai_key,
        task_id,
        questions=False,
    ):
        self.req = req
        self.openai_key = openai_key
        self.task_id = task_id
        self.data = {"data": []}
        self.status = None
        self.iteration = 0
        self.questions = questions

    def _initialize_from_cache(self):
        existing_data = cache.get(self.task_id)
        if existing_data:
            self.data = json.loads(existing_data.get("data", self.data))
            logger.info("Found existing data for task %s", self.task_id)
            logger.info("Existing data total samples: %d", len(self.data))
        else:
            logger.info("No existing data found for task %s", self.task_id)
        self.status = existing_data

    def _fetch_and_update(self, batch_index):
        try:
            if self.questions:
                res = utils.get_question(
                    self.openai_key,
                    min(self.req.num_samples, 20),
                    self.req.content,
                    self.req.model,
                    self.req.system_prompt,
                    self.req.user_prompt,
                )
            else:
                res = utils.get_data(
                    self.openai_key,
                    self.req.labels,
                    min(self.req.num_samples, 20),
                    self.req.valid_data,
                    self.req.invalid_data,
                )
            self.data["data"].extend(res)

            progress = min(100, len(self.data["data"]) / self.req.num_samples * 100)

            self.status = {
                "status": "Processing",
                "Progress": "%s%%" % progress,
                "Detail": "Generating data (Batch %s)" % batch_index,
                "data": json.dumps(self.data),
            }

            if self.questions:
                self.status["content_row"] = self.req.index

            cache.set(self.task_id, self.status)

            logger.info(
                "Saved data to cache for task %s, iteration %d and Batch %s",
                self.task_id,
                self.iteration,
                batch_index,
            )
        except Exception as e:
            logger.error(
                "Failed to fetch data for task %s, iteration %d and Batch %s: %s",
                self.task_id,
                self.iteration,
                batch_index,
                str(e),
            )

    def _fetch_data(self):
        self._initialize_from_cache()
        tasks = []
        batch_size = 20
        num_samples = self.req.num_samples
        num_batches = max(
            1, (num_samples - len(self.data["data"]) + batch_size - 1) // batch_size
        )

        for batch_index in range(num_batches):
            self._fetch_and_update(batch_index)

        logger.info(
            "Iteration Completed. Current Total samples %d", len(self.data["data"])
        )

        if len(self.data["data"]) < num_samples:
            logger.info(
                "Need to fetch more data. Starting new iteration for task %s",
                self.task_id,
            )
            self.iteration += 1
            self._fetch_data()

    def fetch(self):
        self._fetch_data()
        logger.info("Total samples downloaded %d", len(self.data["data"]))
        logger.info("All Data Fetched - Returning data")
        return self.data["data"]
