import json
import os
import re
import sys
from datetime import datetime, time

# Adiciona o diretório raiz do projeto ao Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
from django.db.utils import IntegrityError
from django.utils.text import slugify

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missas.settings")
django.setup()

from missas.core.models import Contact, City, Parish, Schedule, Source  # noqa

# Carrega dados do JSONL do scraper
with open("./paroquias_rs_final.jsonl", encoding="utf-8") as f:
    datas = [json.loads(line) for line in f.readlines()]

# Busca ou cria a fonte de dados
source, _ = Source.objects.get_or_create(
    type=Source.Type.SITE, 
    description="Site da Arquidiocese de Porto Alegre"
)

def create_unique_slug(parish_name, city):
    """Cria um slug único para a paróquia"""
    base_slug = slugify(parish_name)
    slug = base_slug
    counter = 1
    
    while Parish.objects.filter(slug=slug, city=city).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug

print(f"Processando {len(datas)} paróquias do Rio Grande do Sul...")

for d in datas:
    if not d.get("parish_name") or not d.get("city"):
        print(f"Dados incompletos: {d}")
        continue

    # Busca ou cria a cidade
    try:
        city = City.objects.get(name=d["city"], state__short_name="RS")
    except City.DoesNotExist:
        print(f"Cidade não encontrada: {d['city']}")
        continue

    # Cria ou busca a paróquia
    parish_name = d["parish_name"].strip()
    unique_slug = create_unique_slug(parish_name, city)
    
    parish, created = Parish.objects.get_or_create(
        city=city, 
        name=parish_name,
        defaults={'slug': unique_slug}
    )

    if created:
        print(f"Paróquia criada: {parish}")

    # Cria o contato
    try:
        contact, created = Contact.objects.get_or_create(
            parish=parish,
            defaults={
                'email': d.get("email", ""),
                'phone': d.get("phone", ""),
                'whatsapp': d.get("whatsapp", ""),
                'facebook': "",
                'instagram': "",
                'phone2': "",
            }
        )
        
        if created:
            print(f"Contato criado: {contact}")
            
    except IntegrityError as e:
        print(f"Erro ao criar contato para {parish}: {e}")
        continue

    # Processa horários de missa
    for schedule_text in d.get("schedules", []):
        if not schedule_text.strip():
            continue
            
        # Parser simples para horários (pode ser melhorado)
        schedule_text = schedule_text.strip()
        
        # Extrai horários no formato "19h", "18h30", etc.
        time_matches = re.findall(r'(\d{1,2}):?(\d{0,2})h?', schedule_text.lower())
        
        # Mapeia dias da semana
        day_mapping = {
            'domingo': 0, 'segunda': 1, 'terça': 2, 'quarta': 3,
            'quinta': 4, 'sexta': 5, 'sábado': 6
        }
        
        # Busca dias mencionados
        found_days = []
        for day_name, day_num in day_mapping.items():
            if day_name in schedule_text.lower():
                found_days.append(day_num)
        
        # Se não encontrou dias específicos, assume que é válido para todos os dias mencionados
        if not found_days:
            # Tenta extrair padrões como "terça a sábado"
            if 'terça' in schedule_text.lower() and 'sábado' in schedule_text.lower():
                found_days = [2, 3, 4, 5, 6]  # Terça a sábado
            elif 'segunda' in schedule_text.lower() and 'sexta' in schedule_text.lower():
                found_days = [1, 2, 3, 4, 5]  # Segunda a sexta
            else:
                # Se não conseguiu identificar, pula este horário
                print(f"Não foi possível identificar dias em: '{schedule_text}'")
                continue
        
        # Cria schedules para cada horário encontrado
        for time_match in time_matches:
            hour = int(time_match[0])
            minute = int(time_match[1]) if time_match[1] else 0
            
            try:
                start_time = time(hour, minute)
            except ValueError:
                print(f"Horário inválido: {hour}:{minute} em '{schedule_text}'")
                continue
            
            # Cria schedule para cada dia encontrado
            for day in found_days:
                try:
                    schedule, created = Schedule.objects.get_or_create(
                        parish=parish,
                        day=day,
                        start_time=start_time,
                        type=Schedule.Type.MASS,
                        defaults={
                            'source': source,
                            'observation': schedule_text,
                            'location': '',
                            'verified_at': datetime.now().date(),
                        }
                    )
                    
                    if created:
                        print(f"Horário criado: {schedule}")
                        
                except IntegrityError:
                    # Já existe, apenas atualiza a observação se necessário
                    try:
                        existing = Schedule.objects.get(
                            parish=parish, day=day, start_time=start_time
                        )
                        if existing.observation != schedule_text:
                            existing.observation = schedule_text
                            existing.verified_at = datetime.now().date()
                            existing.save()
                            print(f"Horário atualizado: {existing}")
                    except:
                        pass

print("Importação concluída!")
