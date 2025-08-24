import scrapy
import re


class RsSpider(scrapy.Spider):
    name = "rs"
    allowed_domains = ["www.arquipoa.com"]
    
    # Lista com todas as cidades da arquidiocese do Rio Grande do Sul
    cities = [
        {"name": "Alvorada", "value": "3"},
        {"name": "Arambaré", "value": "7"},
        {"name": "Arroio dos Ratos", "value": "8"},
        {"name": "Barão do Triunfo", "value": "9"},
        {"name": "Barra do Ribeiro", "value": "10"},
        {"name": "Butiá", "value": "11"},
        {"name": "Cachoeirinha", "value": "12"},
        {"name": "Camaquã", "value": "13"},
        {"name": "Canoas", "value": "4"},
        {"name": "Cerro Grande do Sul", "value": "14"},
        {"name": "Charqueadas", "value": "6"},
        {"name": "Chuvisca", "value": "15"},
        {"name": "Cristal", "value": "16"},
        {"name": "Eldorado do Sul", "value": "17"},
        {"name": "Esteio", "value": "18"},
        {"name": "General Câmara", "value": "19"},
        {"name": "Glorinha", "value": "20"},
        {"name": "Gravataí", "value": "2"},
        {"name": "Guaíba", "value": "21"},
        {"name": "Mariana Pimentel", "value": "22"},
        {"name": "Minas do Leão", "value": "23"},
        {"name": "Nova Santa Rita", "value": "24"},
        {"name": "Porto Alegre", "value": "1"},
        {"name": "São Jerônimo", "value": "25"},
        {"name": "Sapucaia do Sul", "value": "26"},
        {"name": "Sentinela do Sul", "value": "27"},
        {"name": "Sertão Santana", "value": "28"},
        {"name": "Tapes", "value": "29"},
        {"name": "Viamão", "value": "5"},
    ]
    
    # Configurações de saída
    custom_settings = {
        'FEEDS': {
            'paroquias_rs_final.jsonl': {
                'format': 'jsonlines',
                'encoding': 'utf-8'
            }
        }
    }

    def start_requests(self):
        """
        Primeiro faz GET na página principal, depois POST para cada cidade
        """
        yield scrapy.Request(
            url="https://www.arquipoa.com/paroquias",
            callback=self.make_city_requests
        )
    
    def make_city_requests(self, response):
        """
        Faz uma requisição POST para cada cidade
        """
        for city in self.cities:
            yield scrapy.FormRequest(
                url="https://www.arquipoa.com/pages/filterCity",
                method='POST',
                formdata={'value': city['value']},
                callback=self.parse,
                meta={'city_name': city['name']}
            )

    def parse(self, response):
        """
        Extrai dados das paróquias do Rio Grande do Sul
        """
        city_name = response.meta.get('city_name', '')
        parish_count = 0
        
        # Seleciona todas as divs das paróquias
        for parish_div in response.css('div.col-12.col-sm-6.col-md-8'):
            
            # Extrai o nome da paróquia
            parish_name = parish_div.css('h6::text').get()
            if not parish_name:
                continue
            
            parish_count += 1
            
            # Extrai endereço
            address = parish_div.css('p:first-of-type::text').get() or ""
            
            # Extrai telefone
            phone_raw = parish_div.css('p:nth-of-type(2) a[href^="tel:"]::text').get() or ""
            phone = phone_raw.replace(" ", "").replace("-", "") if phone_raw else ""
            
            # Extrai email
            email_match = parish_div.css('p:nth-of-type(2)').re(r'[\w\.-]+@[\w\.-]+\.[\w]+')
            email = email_match[0] if email_match else ""
            
            # Extrai WhatsApp
            whatsapp = ""
            whatsapp_link = parish_div.css('a[href*="wa.me"]::attr(href)').get()
            if whatsapp_link:
                # Extrai o número do link wa.me/xxxxxxxx
                whatsapp_match = re.search(r'wa\.me/(\d+)', whatsapp_link)
                if whatsapp_match:
                    whatsapp_number = whatsapp_match.group(1)
                    # Verifica o tamanho do número para decidir o prefixo
                    if len(whatsapp_number) in [10, 11]:
                        whatsapp = f"+55{whatsapp_number}"  # Números locais com DDD
                    elif len(whatsapp_number) in [12, 13]:
                        whatsapp = f"+{whatsapp_number}"    # Números já com código do país
                    else:
                        whatsapp = f"+{whatsapp_number}"    # Outros casos, só adiciona +
            
            # Extrai horários de missa
            schedules = []
            # Busca por parágrafo que contém "Horário" seguido pelos horários
            paragraphs = parish_div.css('p')
            found_schedule_header = False
            
            for p in paragraphs:
                p_text = p.css('::text').get()
                if p_text and 'horário' in p_text.lower() and 'missa' in p_text.lower():
                    found_schedule_header = True
                    continue
                
                # Se encontrou o cabeçalho, pega os próximos parágrafos com horários
                if found_schedule_header and p_text:
                    text = p_text.strip()
                    if text and (any(day in text.lower() for day in ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']) or 'h' in text):
                        schedules.append(text)
                    elif text and not any(word in text.lower() for word in ['tel', 'telefone', '@', 'email', 'endereço']):
                        # Para de buscar se encontrar um parágrafo que não é horário
                        break
            
            # Retorna os dados estruturados
            yield {
                'parish_name': parish_name.strip(),
                'city': city_name,
                'address': address.strip(),
                'phone': phone.strip(),
                'email': email.strip(),
                'whatsapp': whatsapp.strip(),
                'schedules': schedules,
            }
        
        # Log do resultado
        self.logger.info(f"Processadas {parish_count} paróquias em {city_name}")