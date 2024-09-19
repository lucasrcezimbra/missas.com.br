.PHONY: dumpdata loaddata

dumpdata:
		poetry run python manage.py dumpdata --indent 2 core.State > missas/core/fixtures/states.json
		poetry run python manage.py dumpdata --indent 2 core.City > missas/core/fixtures/cities.json
		poetry run python manage.py dumpdata --indent 2 core.Source > missas/core/fixtures/sources.json
		poetry run python manage.py dumpdata --indent 2 core.Parish > missas/core/fixtures/parishes_natal.json
		poetry run python manage.py dumpdata --indent 2 core.Schedule > missas/core/fixtures/schedules_natal.json

loaddata:
		poetry run python manage.py loaddata ./missas/core/fixtures/states.json
		poetry run python manage.py loaddata ./missas/core/fixtures/cities.json
		poetry run python manage.py loaddata ./missas/core/fixtures/sources.json
		poetry run python manage.py loaddata ./missas/core/fixtures/parishes_natal.json
		poetry run python manage.py loaddata ./missas/core/fixtures/schedules_natal.json
