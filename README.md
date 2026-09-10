# Missas

<!--toc:start-->
- [Contributing](#contributing)
  - [Installation](#installation)
  - [Test](#test)
  - [Run](#run)
  - [Coverage](#coverage)
  - [Scrapers](#scrapers)
  - [WhatsApp Import](#whatsapp-import)
- [Sponsorship](#sponsorship)
<!--toc:end-->

Website brings together Mass and confession times for Catholic parishes
throughout Brazil (maybe others in the future).

![](./contrib/screenshot-homepage.png)

![](./contrib/screenshot-schedules.png)

## Contributing
### Installation
Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

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

### Coverage
```bash
make coverage
```

### Scrapers
```shell
uv run --group scrapers scrapy runspider contrib/scraper_natal.py -o natal.jsonl
```

### WhatsApp Import
`contrib/import.py` parses manually copied WhatsApp messages using an LLM, asks
for confirmation, and updates the database. The script contains instructions
for copying messages from WhatsApp Web.

Running:

Copy the phone number and messages, then run a command like this:
```shell
# example
uv run --group scrapers python contrib/import.py '+551298765432' '[17:23, 02/12/2024] You:
Bom dia.

Aqui é o Lucas do site missas.com.br. Estamos atualizando o nosso site com as informações sobre as paróquias da Arquidiocese de Natal para ajudar os fiéis a encontrar horários de missas e confissões.

Você poderia me passar os horários de missas e confissões na sua paróquia?

Desde já obrigado.
[15:42, 27/12/2024] +55 12 9876-5432:
Bom dia!
Perdão pela demora.
[15:44, 27/12/2024] +55 12 9876-5432:
Confissões de terça a sexta, 09h às 12h - SECRETARIA PAROQUIAL
Horários de missas na Igreja Matriz: 07h 19h (domigos)
17h30 (terça, quinta e sexta)'
```


## Sponsorship

Sentry supports this project with their [Open-Source Sponsorship Plan](https://sentry.io/for/open-source/)

![](./contrib/sentry.png)
