import asyncio
import logging
import json
from rest_framework.views import APIView
from ..models import GenerationAndCommitRequest

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
handler.recursion_depth = 100

logger.addHandler(handler)

class DataFetcher(APIView):
    MAX_CONCURRENT_FETCHES = 10
    MAX_ITERATION_LIMIT = 15
    def __init__(
            self,
            req: GenerationAndCommitRequest,
            openai_key,
            redis,
            task_id,
            questions=False,
    ):
        self.req = req
        self.openai_key = openai_key
        self.redis = redis
        self.task_id = task_id
        self.data = {"data": []}
        self.semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_FETCHES)
        self.status = None
        self.iteration = 0
        self.questions = questions

    async def _initialize_from_redis(self):
        loop = asyncio.get_running_loop()
        existing_data = await loop.run_in_executor(None, self.redis.hgetall, self.task_id)
        if existing_data and "data" in existing_data:
            self.data = json.loads(existing_data.get("data", self.data))
            logger.info("Found existing data for task %s", self.task_id)
            logger.info("Existing data total samples: %d", len(self.data))
        else:
            logger.info("No existing data found for task %s", self.task_id)
        self.status = existing_data

    async def _fetch_and_update(self, batch_index):
        async with self.semaphore:
            try:
                if self.questions:
                    res = await utils.get_question(
                        self.openai_key,
                        self.req.num_samples if self.req.num_samples < 20 else 20,
                        self.req.content,
                        self.req.model,
                        self.req.system_prompt,
                        self.req.user_prompt,
                    )
                else:
                    res = await utils.get_data(
                        self.openai_key,
                        self.req.labels,
                        self.req.num_samples if self.req.num_samples < 20 else 20,
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

                await self.redis.hset(
                    self.task_id,
                    mapping=self.status,
                )

                logger.info(
                    "Saved data to redis for task %s, iteration %d and Batch %s",
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

    async def _fetch_data(self):
        await self._initialize_from_redis()
        tasks = []
        batch_size = 20

        if 'num_samples' not in self.req:
            logger.error("Request data does not contain 'num_samples' attribute")
            return

        num_samples = self.req['num_samples']
        num_batches = max(
            1, (num_samples - len(self.data["data"]) + batch_size - 1) // batch_size
        )

        for batch_index in range(num_batches):
            task = self._fetch_and_update(batch_index)
            tasks.append(task)

        await asyncio.gather(*tasks)

        logger.info(
            "Iteration Completed. Current Total samples %d", len(self.data["data"])
        )

        if len(self.data["data"]) < num_samples:
            logger.info(
                "Need to fetch more data. Starting new iteration for task %s",
                self.task_id,
            )
            self.iteration += 1
            if self.iteration < self.MAX_ITERATION_LIMIT:
                await self._fetch_data()
            else:
                logger.warning("Maximum iteration limit reached. Terminating fetching.")

    async def fetch(self):
        if 'num_samples' not in self.req:
            logger.error("Request data does not contain 'num_samples' attribute")
            return

        await self._fetch_data()
        logger.info("Total samples downloaded %d", len(self.data["data"]))
        logger.info("All Data Fetched - Returning data")
