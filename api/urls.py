from django.contrib import admin
from django.urls import path

from api.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('generate_data/', generate_data, name='generate_data'),
    path('generate_and_push_data/', generate_and_push_data, name='generate_and_push_data'),

]