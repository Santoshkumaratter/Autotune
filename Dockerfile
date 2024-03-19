FROM python:3.9

ENV PYTHONUNBUFFERED 1

WORKDIR /code

COPY . /code

RUN pip install -r requirements.txt

EXPOSE 8000

# Run django-admin.py when the container launches
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
