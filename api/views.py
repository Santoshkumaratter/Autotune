from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import AuthenticationFailed
from .models import GenerationAndCommitRequest
import uuid
from django.conf import settings

from .serializer import GenerationAndCommitRequestSerializer
from .tasks.data import generate_data

class SampleGenerationView(APIView):
    permission_classes = [AllowAny]

    async def post(self, request, format=None):
        req_data = request.data
        openai_key = request.headers.get('X-OpenAI-Key')

        if openai_key is None:
            raise AuthenticationFailed('X-OpenAI-Key header missing')

        serializer = GenerationAndCommitRequestSerializer(data=req_data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        generation_request = GenerationAndCommitRequest.objects.create(**validated_data)

        task_id = str(uuid.uuid4())

        data = await generate_data(settings.REDIS_POOL, task_id, req_data, openai_key)

        return Response({"response": data}, status=status.HTTP_202_ACCEPTED)
