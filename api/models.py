from django.db import models

from django.core.exceptions import ValidationError

def validate_split_choice(value):
    valid_choices = [choice[0] for choice in GenerationAndCommitRequest.SPLIT_CHOICES]
    if value not in valid_choices:
        raise ValidationError(f"'{value}' is not a valid choice for 'split'.")

class GenerationAndCommitRequest(models.Model):
    SPLIT_CHOICES = [
        ('train', 'Train'),
        ('validation', 'Validation'),
        ('test', 'Test')
    ]

    num_samples = models.IntegerField()
    repo = models.CharField(max_length=255)
    split = models.CharField(max_length=20, validators=[validate_split_choice], default='train')
    labels = models.JSONField(null=True, blank=True)
    valid_data = models.JSONField(null=True, blank=True)
    invalid_data = models.JSONField(null=True, blank=True)


class GenerationAndUpdateRequest(models.Model):
    SPLIT_CHOICES = [
        ('train', 'Train'),
        ('validation', 'Validation'),
        ('test', 'Test')
    ]

    num_samples = models.IntegerField()
    repo = models.CharField(max_length=255)
    split = models.CharField(max_length=20, choices=SPLIT_CHOICES, default='train')
    labels = models.JSONField(null=True, blank=True)
    valid_data = models.JSONField(null=True, blank=True)
    invalid_data = models.JSONField(null=True, blank=True)


class ChatViewRequest(models.Model):
    TASK_CHOICES = [
        ('text_classification', 'Text Classification'),
        ('seq2seq', 'Seq2Seq')
    ]

    prompt = models.TextField()
    num_samples = models.IntegerField()
    task = models.CharField(max_length=20, choices=TASK_CHOICES, default='text_classification')
    num_labels = models.IntegerField(default=2)


class QuestionCreationRequest(models.Model):
    num_samples = models.IntegerField()
    repo = models.CharField(max_length=255)
    SPLIT_CHOICES = [
        ('train', 'Train'),
        ('validation', 'Validation'),
        ('test', 'Test')
    ]
    split = models.CharField(max_length=20, choices=SPLIT_CHOICES, default='train')
    system_prompt = models.TextField(null=True, blank=True)
    user_prompt = models.TextField(null=True, blank=True)
    content = models.JSONField()
    index = models.IntegerField(null=True, blank=True)
    model = models.CharField(max_length=50, default="gpt-3.5-turbo")
    multiple_chunks = models.BooleanField(default=False)
    combined_index = models.CharField(max_length=50, null=True, blank=True)


class QuestionUpdationRequest(models.Model):
    num_samples = models.IntegerField()
    repo = models.CharField(max_length=255)
    SPLIT_CHOICES = [
        ('train', 'Train'),
        ('validation', 'Validation'),
        ('test', 'Test')
    ]
    split = models.CharField(max_length=20, choices=SPLIT_CHOICES, default='train')
    system_prompt = models.TextField(null=True, blank=True)
    user_prompt = models.TextField(null=True, blank=True)
    content = models.JSONField()
    index = models.IntegerField(null=True, blank=True)
    model = models.CharField(max_length=50, default="gpt-3.5-turbo")
    multiple_chunks = models.BooleanField(default=False)
    combined_index = models.CharField(max_length=50, null=True, blank=True)
    bulk_process = models.BooleanField(default=False)

class ModelData(models.Model):
    TASK_CHOICES = [
        ('text_classification', 'Text Classification'),
        ('seq2seq', 'Seq2Seq')
    ]
    dataset = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    epochs = models.FloatField(default=1)
    save_path = models.CharField(max_length=255)
    task = models.CharField(max_length=20, choices=TASK_CHOICES)
    version = models.CharField(max_length=50, default="main")

