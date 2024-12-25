# Missas

![](./contrib/screenshot.png)

## Installation
```bash
git clone git@github.com:lucasrcezimbra/missas.com.br.git
cd missas.com.br
make install
```

### Test
```bash
make test
```

### Run
```bash
make dev
```

#### Scrapers
```shell
poetry run scrapy runspider contrib/scraper_natal.py -o natal.jsonl
```
