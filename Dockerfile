FROM python:3.11-slim-buster

RUN apt-get update

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# COPY ./initials/initial.sh /docker-entrypoint.d/initial.sh

# RUN chmod +x /docker-entrypoint.d/initial.sh

RUN mkdir build

# We create folder named build for our app.
WORKDIR /build

COPY ./app ./app
COPY ./initials ./initials
COPY ./requirements.txt .
COPY ./alembic.ini .

# We copy our app folder to the /build

RUN pip install -r requirements.txt

# RUN chmod +x ./initials/initial.sh

CMD ["/bin/bash", "-c", "echo python initials/db_starter.py;echo alembic upgrade heads;echo python initials/initial_data.py;echo sanic app.main:app --host 0.0.0.0 --port 8000"]

# CMD ["bash", "./initials/initial.sh"]

ENV PYTHONPATH=/build

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
