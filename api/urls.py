from django.urls import path
from .views import (
    SampleGenerationView,
    ChatViewView,
    ChatCompletionView,
    ChatUpdationView,
    QuestionGenerationView,
    QuestionUpdationView,
    TrainModelView,
    CommitView,
    TaskProgressView,
)

urlpatterns = [
    path('sample/', SampleGenerationView.as_view(), name='sample_generation'),
    path('data/view/', ChatViewView.as_view(), name='chat_view'),
    path('data/', ChatCompletionView.as_view(), name='chat_completion'),
    path('data/update/', ChatUpdationView.as_view(), name='chat_updation'),
    path('question/', QuestionGenerationView.as_view(), name='question_generation'),
    path('question/update/', QuestionUpdationView.as_view(), name='question_updation'),
    path('train/', TrainModelView.as_view(), name='train_model'),
    path('commit/', CommitView.as_view(), name='commit_view'),
    path('progress/<str:task_id>/', TaskProgressView.as_view(), name='task_progress'),
]
