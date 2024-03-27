import json
import asyncio
import aioredis
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .tasks import train_model

@api_view(['POST'])
def train_task_view(request):
    req_data = request.data
    api_key = req_data.get("api_key")

    task = train_model.apply_async(args=[req_data, api_key])

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    redis_pool = loop.run_until_complete(aioredis.from_url("redis://localhost", decode_responses=True))

    loop.run_until_complete(redis_pool.hset(str(task.id), mapping={"status": "RUNNING"}))

    loop.run_until_complete(redis_pool.close())

    return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)
