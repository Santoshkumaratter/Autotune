import os
from pathlib import Path
import aioredis

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-)02zx_h(=dw_^$hb=kbaye%lp+#oh3-o%psk0do6-ornvp8l2o'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'api',
    'rest_framework',
]
from django.core.signals import request_started, request_finished
from django.http import HttpRequest, HttpResponse
from django.core.handlers.wsgi import WSGIRequest
from typing import Callable, Awaitable, Union
import logging
import time
import random
import string
import aioredis
from django.conf import settings

logger = logging.getLogger(__name__)

# Redis connection pool
REDIS_POOL = None

# Redis ko initialize karne ka function
def initialize_redis_pool():
    global REDIS_POOL
    REDIS_POOL = aioredis.from_url("redis://localhost", decode_responses=True)

# Custom middleware for logging HTTP requests
def log_requests(get_response: Callable) -> Callable:
    async def middleware(request: Union[WSGIRequest, HttpRequest], next: Callable) -> Awaitable:
        idem = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        logger.info("rid=%s start request path=%s", idem, request.path)
        start_time = time.time()

        response = await next(request)

        process_time = (time.time() - start_time) * 1000
        formatted_process_time = "{0:.2f}".format(process_time)
        logger.info(
            "rid=%s completed_in=%sms status_code=%s",
            idem,
            formatted_process_time,
            response.status_code,
        )

        return response

    return middleware

# Django ka startup event use karke Redis pool ko initialize karein
def startup_event(sender, **kwargs):
    initialize_redis_pool()

# Django ka shutdown event use karke Redis pool ko close karein
def shutdown_event(sender, **kwargs):
    if REDIS_POOL is not None:
        REDIS_POOL.close()

# Django settings.py mein startup aur shutdown event ko configure karein
request_started.connect(startup_event)
request_finished.connect(shutdown_event)

# Custom middleware ko MIDDLEWARE list mein add karein
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'autotune.settings.log_requests',
]

# Redis ko use karne ke liye REDIS_POOL ko import karein
from django.conf import settings

# Django ka startup event use karke Redis pool ko initialize karein
def startup_event(sender, **kwargs):
    initialize_redis_pool()

# Django ka shutdown event use karke Redis pool ko close karein
def shutdown_event(sender, **kwargs):
    if REDIS_POOL is not None:
        REDIS_POOL.close()

# Django settings.py mein startup aur shutdown event ko configure karein
from django.core.signals import request_started, request_finished

request_started.connect(startup_event)
request_finished.connect(shutdown_event)

# Custom middleware for logging HTTP requests
import logging
import time
import random
import string
from django.http import HttpRequest
from django.core.handlers.wsgi import WSGIRequest
from typing import Callable
from typing import Awaitable
from typing import Union

logger = logging.getLogger(__name__)

def log_requests(get_response: Callable) -> Callable:
    async def middleware(request: Union[WSGIRequest, HttpRequest], next: Callable) -> Awaitable:
        idem = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        logger.info("rid=%s start request path=%s", idem, request.path)
        start_time = time.time()

        response = await next(request)

        process_time = (time.time() - start_time) * 1000
        formatted_process_time = "{0:.2f}".format(process_time)
        logger.info(
            "rid=%s completed_in=%sms status_code=%s",
            idem,
            formatted_process_time,
            response.status_code,
        )

        return response

    return middleware

MIDDLEWARE.insert(0, 'autotune.settings.log_requests')

ASGI_APPLICATION = 'autotune.asgi.application'


ROOT_URLCONF = 'autotune.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'autotune.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgress',
        'USER': 'postgres',
        'PASSWORD': 'root',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Redis connection pool
REDIS_POOL = None

# Redis ko initialize karne ka function
def initialize_redis_pool():
    global REDIS_POOL
    REDIS_POOL = aioredis.from_url("redis://localhost", decode_responses=True)

def startup_event(sender, **kwargs):
    initialize_redis_pool()

# Django ka shutdown event use karke Redis pool ko close karein
def shutdown_event(sender, **kwargs):
    if REDIS_POOL is not None:
        REDIS_POOL.close()

# Django settings.py mein startup aur shutdown event ko configure karein
from django.core.signals import request_started, request_finished

request_started.connect(startup_event)
request_finished.connect(shutdown_event)

# Custom middleware for logging HTTP requests
import logging
import time
import random
import string
from django.http import HttpRequest
from django.core.handlers.wsgi import WSGIRequest
from typing import Callable
from typing import Awaitable
from typing import Union
from typing import Optional

logger = logging.getLogger(__name__)

def log_requests(get_response: Callable) -> Callable:
    async def middleware(request: Union[WSGIRequest, HttpRequest], next: Callable) -> Awaitable:
        idem = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        logger.info("rid=%s start request path=%s", idem, request.path)
        start_time = time.time()

        response = await next(request)

        process_time = (time.time() - start_time) * 1000
        formatted_process_time = "{0:.2f}".format(process_time)
        logger.info(
            "rid=%s completed_in=%sms status_code=%s",
            idem,
            formatted_process_time,
            response.status_code,
        )

        return response

    return middleware

MIDDLEWARE.insert(0, 'autotune.settings.log_requests')

ASGI_APPLICATION = 'autotune.asgi.application'
