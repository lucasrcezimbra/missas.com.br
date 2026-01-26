.DEFAULT_GOAL := dev
.PHONY: build check-template coverage dbdump dbload dev install lint run test update-template worktree

build:
	poetry install --without=dev --without=scrapers
	poetry run python manage.py collectstatic --no-input

coverage:
	poetry run pytest --cov=missas --cov-branch --cov-report=xml

dbdump:
	poetry run python manage.py dumpdata --indent 2 core.State > missas/core/fixtures/states.json
	poetry run python manage.py dumpdata --indent 2 core.City > missas/core/fixtures/cities.json
	poetry run python manage.py dumpdata --indent 2 core.Source > missas/core/fixtures/sources.json
	poetry run python manage.py dumpdata --indent 2 core.Parish > missas/core/fixtures/parishes_natal.json
	poetry run python manage.py dumpdata --indent 2 core.Contact > missas/core/fixtures/contacts_natal.json
	poetry run python manage.py dumpdata --indent 2 core.Location > missas/core/fixtures/locations_natal.json
	poetry run python manage.py dumpdata --indent 2 core.Schedule > missas/core/fixtures/schedules_natal.json

dbload:
	poetry run python manage.py loaddata ./missas/core/fixtures/states.json
	poetry run python manage.py loaddata ./missas/core/fixtures/cities.json
	poetry run python manage.py loaddata ./missas/core/fixtures/sources.json
	poetry run python manage.py loaddata ./missas/core/fixtures/parishes_natal.json
	poetry run python manage.py loaddata ./missas/core/fixtures/contacts_natal.json
	poetry run python manage.py loaddata ./missas/core/fixtures/locations_natal.json
	poetry run python manage.py loaddata ./missas/core/fixtures/schedules_natal.json

dbmigrate:
	poetry run python manage.py migrate --database=old
	poetry run python manage.py migrate --database=default

dev:
	make dbmigrate
	poetry run python manage.py runserver

install:
	poetry install
	poetry run pre-commit install
	poetry run pre-commit install-hooks
	cp contrib/env-sample .env
	make dbmigrate
	make dbload

lint:
	poetry run pre-commit run -a
	poetry run pytest --dead-fixtures

run:
	make dbmigrate
	poetry run python manage.py createcachetable
	poetry run gunicorn missas.wsgi:application

test:
	poetry run pytest

update-template:
	poetry run cruft update --skip-apply-ask

worktree:
	@if [ -z "$(NAME)" ]; then \
		echo "Error: NAME is required. Usage: make worktree NAME=branch-name"; \
		exit 1; \
	fi
	git worktree add $(NAME) -b $(NAME)
	cp -r .claude $(NAME)/.claude
	cd $(NAME) && make install
