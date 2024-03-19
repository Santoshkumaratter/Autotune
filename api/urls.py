from django.contrib import admin
from django.urls import path

from api import views
from api.views import SampleGenerationView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sample/', SampleGenerationView.as_view(), name='sample-generation'),
]
