ifneq (,$(wildcard ./.env))
include .env
export 
ENV_FILE_PARAM = --env-file .env

endif

serv:
	sanic app.main:app --debug --reload

mmig:
	alembic revision --autogenerate 

mig:
	alembic upgrade heads

test:
	pytest --verbose --disable-warnings -vv -x --timeout=10