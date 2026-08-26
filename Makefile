.DEFAULT_GOAL := dev
.PHONY: build check-template coverage dbdump dbload dev install lint run test update-template worktree

build:
	uv sync --frozen --no-dev
	uv run --no-sync python manage.py collectstatic --no-input

coverage:
	uv run pytest --cov=missas --cov-branch --cov-report=xml

dbdump:
	uv run python manage.py dumpdata --indent 2 core.State > missas/core/fixtures/states.json
	uv run python manage.py dumpdata --indent 2 core.City > missas/core/fixtures/cities.json
	uv run python manage.py dumpdata --indent 2 core.Source > missas/core/fixtures/sources.json
	uv run python manage.py dumpdata --indent 2 core.Parish > missas/core/fixtures/parishes_natal.json
	uv run python manage.py dumpdata --indent 2 core.Contact > missas/core/fixtures/contacts_natal.json
	uv run python manage.py dumpdata --indent 2 core.Location > missas/core/fixtures/locations_natal.json
	uv run python manage.py dumpdata --indent 2 core.Schedule > missas/core/fixtures/schedules_natal.json

dbload:
	uv run python manage.py loaddata ./missas/core/fixtures/states.json
	uv run python manage.py loaddata ./missas/core/fixtures/cities.json
	uv run python manage.py loaddata ./missas/core/fixtures/sources.json
	uv run python manage.py loaddata ./missas/core/fixtures/parishes_natal.json
	uv run python manage.py loaddata ./missas/core/fixtures/contacts_natal.json
	uv run python manage.py loaddata ./missas/core/fixtures/locations_natal.json
	uv run python manage.py loaddata ./missas/core/fixtures/schedules_natal.json

dbmigrate:
	uv run python manage.py migrate

dev:
	make dbmigrate
	uv run python manage.py runserver

install:
	uv sync --locked --all-groups
	uv run --no-sync pre-commit install
	uv run --no-sync pre-commit install-hooks
	cp contrib/env-sample .env
	UV_NO_SYNC=1 make dbmigrate
	UV_NO_SYNC=1 make dbload

lint:
	uv run pre-commit run -a
	uv run pytest --dead-fixtures

run:
	uv run --no-sync python manage.py migrate
	uv run --no-sync python manage.py createcachetable
	uv run --no-sync gunicorn missas.wsgi:application

test:
	uv run pytest

update-template:
	uv run cruft update --skip-apply-ask

worktree:
	@if [ -z "$(NAME)" ]; then \
		echo "Error: NAME is required. Usage: make worktree NAME=branch-name"; \
		exit 1; \
	fi
	git worktree add $(NAME) -b $(NAME)
	cp -r .claude $(NAME)/.claude
	cd $(NAME) && make install
