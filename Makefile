ifneq (,$(wildcard ./.env))
include .env
export 
ENV_FILE_PARAM = --env-file .env

endif

build:
	docker-compose up --build -d --remove-orphans

up:
	docker-compose up -d

down:
	docker-compose down

show-logs:
	docker-compose logs

serv:
	sanic app.main:app --debug --reload

mmig: # run with "make mmig" or "make mmig message='migration message'"
	if [ -z "$(message)" ]; then \
		alembic revision --autogenerate; \
	else \
		alembic revision --autogenerate -m "$(message)"; \
	fi
	
mig:
	alembic upgrade heads

init:
	python initials/initial_data.py

tests:
	pytest --verbose --disable-warnings -vv -x --timeout=10

requirements:
	pip install -r requirements.txt

# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MDQzODA3NzIsInVzZXJfaWQiOiIzN2Y0YjU2YS02MTdiLTQwMTUtYmEzMi02YzA4OTgzYjg5MjAifQ.pG_i3EH2H7rB_4DmyEqNoSK9ljsNGWRQXp7mQjRkme0