from rest_framework import serializers
from api.models import *

class GenerationAndCommitRequestSerializer(serializers.ModelSerializer):
    split = serializers.ChoiceField(choices=GenerationAndCommitRequest.SPLIT_CHOICES)

    class Meta:
        model = GenerationAndCommitRequest
        fields = '__all__'
    def validate_split(self, value):
        valid_choices = [choice[0] for choice in GenerationAndCommitRequest.SPLIT_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(f"'{value}' is not a valid choice for 'split'.")
        return value


class GenerationAndUpdateRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenerationAndUpdateRequest
        fields = '__all__'


class ChatViewRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatViewRequest
        fields = '__all__'


class QuestionCreationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionCreationRequest
        fields = '__all__'


class QuestionUpdationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionUpdationRequest
        fields = '__all__'


class ModelDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelData
        fields = '__all__'




class GenerationRequestSerializer(serializers.Serializer):
    api_key = serializers.CharField(max_length=255)
    labels = serializers.ListField(child=serializers.CharField())
    num_samples = serializers.IntegerField()
    valid_data = serializers.ListField(required=False)
    invalid_data = serializers.ListField(required=False)


class GenerationResponseSerializer(serializers.Serializer):
    data = serializers.ListField(child=serializers.DictField())
