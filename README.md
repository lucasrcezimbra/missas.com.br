# Missas


## Installation
```bash
git clone git@github.com:lucasrcezimbra/missas.git
cd missas
docker-compose up -d
poetry install
poetry run pre-commit install
cp contrib/env-sample .env
poetry run python manage.py migrate
```

### Test
```bash
poetry run pytest
```

### Run
```bash
poetry run manage.py runserver
```

#### Scrapers
```shell
poetry run scrapy runspider contrib/scraper_natal.py -o natal.jsonl
```
