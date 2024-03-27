import json
import logging
import random
import string
import time
import uuid

import aioredis
from celery.result import AsyncResult
from django.http import JsonResponse
from django.views.generic import View
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from .tasks.data import *
from .serializer import *


logger = logging.getLogger(__name__)

import redis

class SampleGenerationView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def post(self, request):
        print("Request data:", request.data)
        split_choices = [choice[0] for choice in GenerationAndCommitRequest.SPLIT_CHOICES]
        if 'split' in request.data and request.data['split'] not in split_choices:
            return Response({"split": ["Invalid choice for 'split'."]}, status=400)

        serializer = GenerationAndCommitRequestSerializer(data=request.data)
        if serializer.is_valid():
            print("Serializer is valid")
            task_id = str(uuid.uuid4())
            print("Task ID:", task_id)
            redis_client = redis.Redis(host='localhost', port=6379, db=0)
            redis_client.hset(
                task_id, mapping={"status": "Starting", "Progress": "None", "Detail": "None"}
            )

            # GenerateDataView.apply_async(args=[redis_pool, task_id, serializer.validated_data])
            return Response({"task_id": task_id}, status=202)
        else:
            print("Serializer errors:", serializer.errors)  # Print serializer errors for debugging
            return Response(serializer.errors, status=400)


class ChatViewView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatViewRequestSerializer(data=request.data)
        if serializer.is_valid():
            task_id = str(uuid.uuid4())
            redis_pool = aioredis.from_url("redis://localhost", decode_responses=True)
            redis_pool.hset(
                task_id, mapping={"status": "Starting", "Progress": "None", "Detail": "None"}
            )
            generate_data.apply_async(args=[redis_pool, task_id, serializer.validated_data])
            return Response({"task_id": task_id}, status=202)
        else:
            return Response(serializer.errors, status=400)


class ChatCompletionView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GenerationAndCommitRequestSerializer(data=request.data)
        if serializer.is_valid():
            task_id = str(uuid.uuid4())
            redis_pool = aioredis.from_url("redis://localhost", decode_responses=True)
            redis_pool.hset(
                task_id, mapping={"status": "Starting", "Progress": "None", "Detail": "None"}
            )
            generate_and_push_data.apply_async(
                args=[redis_pool, task_id, serializer.validated_data]
            )
            return Response({"task_id": task_id}, status=202)
        else:
            return Response(serializer.errors, status=400)


class ChatUpdationView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = GenerationAndUpdateRequestSerializer(data=request.data)
        if serializer.is_valid():
            task_id = str(uuid.uuid4())
            redis_pool = aioredis.from_url("redis://localhost", decode_responses=True)
            redis_pool.hset(
                task_id, mapping={"status": "Starting", "Progress": "None", "Detail": "None"}
            )
            generate_and_update_data.apply_async(
                args=[redis_pool, task_id, serializer.validated_data]
            )
            return Response({"task_id": task_id}, status=202)
        else:
            return Response(serializer.errors, status=400)


class QuestionGenerationView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = QuestionCreationRequestSerializer(data=request.data)
        if serializer.is_valid():
            task_id = str(uuid.uuid4())
            redis_pool = aioredis.from_url("redis://localhost", decode_responses=True)
            redis_pool.hset(
                task_id, mapping={"status": "Starting", "Progress": "None", "Detail": "None"}
            )
            generate_and_push_questions.apply_async(
                args=[redis_pool, task_id, serializer.validated_data]
            )
            return Response({"task_id": task_id}, status=202)
        else:
            return Response(serializer.errors, status=400)


class QuestionUpdationView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = QuestionUpdationRequestSerializer(data=request.data)
        if serializer.is_valid():
            task_id = str(uuid.uuid4())
            redis_pool = aioredis.from_url("redis://localhost", decode_responses=True)
            redis_pool.hset(
                task_id, mapping={"status": "Starting", "Progress": "None", "Detail": "None"}
            )
            generate_and_update_questions.apply_async(
                args=[redis_pool, task_id, serializer.validated_data]
            )
            return Response({"task_id": task_id}, status=202)
        else:
            return Response(serializer.errors, status=400)


class TrainModelView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ModelDataSerializer(data=request.data)
        if serializer.is_valid():
            task_id = str(uuid.uuid4())
            celery_app.send_task("worker.train_task", args=[serializer.validated_data])
            return Response({"task_id": task_id}, status=202)
        else:
            return Response(serializer.errors, status=400)


class CommitView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        repo_id = request.query_params.get('repo_id', None)
        if not repo_id:
            return Response({"error": "repo_id parameter is required."}, status=400)

        api = HfApi()
        try:
            commit_info = api.list_repo_commits(repo_id)
        except Exception as e:
            return Response({"error": str(e)}, status=404)

        commit_info = [
            {"version": item.commit_id, "date": item.created_at}
            for item in commit_info
            if "pytorch_model.bin" in item.title
        ]
        return Response({"commit_info": commit_info})

class TaskProgressView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        res = aioredis.from_url("redis://localhost", decode_responses=True).hgetall(task_id)
        if not res:
            return Response({"error": "Task not found."}, status=404)

        if "handler" in res and res["handler"] == "Celery":
            cres = AsyncResult(task_id, app=celery_app)
            if str(cres.status) == "SUCCESS":
                if isinstance(res["logs"], str):
                    logs = json.loads(res["logs"])
                else:
                    logs = res["logs"]
                return Response({"status": res["status"], "response": logs})
            return Response({"status": str(cres.status), "response": cres.info})

        else:
            try:
                if isinstance(res["Detail"], str):
                    detail = json.loads(res["Detail"])
                    return Response({"status": res["status"], "response": detail["data"]})
            except Exception as e:
                pass

        return Response(
            {"status": res["status"], "response": {"Detail": res["Detail"], "Progress": res["Progress"]}}
        )

