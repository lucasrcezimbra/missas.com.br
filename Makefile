.DEFAULT_GOAL := dev
.PHONY: build check-template coverage dbdump dbload dev install lint run test update-template

build:
	poetry install --without=dev --without=scrapers
	poetry run python manage.py collectstatic --no-input
	poetry run python manage.py migrate

coverage:
	docker compose up -d
	poetry run pytest --cov=missas --cov-branch --cov-report=xml

dbdump:
	poetry run python manage.py dumpdata --indent 2 core.State > missas/core/fixtures/states.json
	poetry run python manage.py dumpdata --indent 2 core.City > missas/core/fixtures/cities.json
	poetry run python manage.py dumpdata --indent 2 core.Source > missas/core/fixtures/sources.json
	poetry run python manage.py dumpdata --indent 2 core.Parish > missas/core/fixtures/parishes_natal.json
	poetry run python manage.py dumpdata --indent 2 core.Contact > missas/core/fixtures/contacts_natal.json
	poetry run python manage.py dumpdata --indent 2 core.Schedule > missas/core/fixtures/schedules_natal.json

dbload:
	poetry run python manage.py loaddata ./missas/core/fixtures/states.json
	poetry run python manage.py loaddata ./missas/core/fixtures/cities.json
	poetry run python manage.py loaddata ./missas/core/fixtures/sources.json
	poetry run python manage.py loaddata ./missas/core/fixtures/parishes_natal.json
	poetry run python manage.py loaddata ./missas/core/fixtures/contacts_natal.json
	poetry run python manage.py loaddata ./missas/core/fixtures/schedules_natal.json

dev:
	docker compose up -d
	poetry run python manage.py migrate
	poetry run python manage.py runserver

install:
	docker compose up -d
	poetry install
	poetry run pre-commit install
	poetry run pre-commit install-hooks
	cp contrib/env-sample .env
	poetry run python manage.py migrate
	make dbload

lint:
	poetry run pre-commit run -a

run:
	poetry run gunicorn missas.wsgi:application

test:
	docker compose up -d
	poetry run pytest

update-template:
	poetry run cruft update --skip-apply-ask
