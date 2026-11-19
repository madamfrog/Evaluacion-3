import os
import django
import csv

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CallCenterGamer.settings')
django.setup()

from online.models import PeliculaNetflix

print("Cargando películas a la base de datos desde el archivo CSV...")

# Opcional: Limpiamos la tabla antes de cargar para evitar duplicados viejos
PeliculaNetflix.objects.all().delete()

contador = 0
with open('server/database.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        titulo = row.get('title') or row.get('Title') or row.get('TITULO') or row.get('name')
        if not titulo:
            continue
            
        # Generamos o capturamos el show_id único para cada película
        show_id = row.get('show_id') or row.get('id') or f"s{contador+1}"
        
        descripcion = row.get('description') or row.get('Description') or row.get('DESCRIPCION') or 'Sin descripción disponible.'
        fecha = row.get('release_date') or row.get('release_year') or row.get('year') or '2026'
        tipo = row.get('type') or row.get('type_show') or 'Película'
        director = row.get('director') or 'Netflix Original'

        PeliculaNetflix.objects.update_or_create(
            show_id=str(show_id).strip(),
            defaults={
                'title': titulo.strip(),
                'description': descripcion.strip(),
                'release_date': str(fecha).strip(),
                'type_show': str(tipo).strip(),
                'director': str(director).strip(),
            }
        )
        contador += 1

print(f"¡Listo! Se han guardado {contador} películas correctamente en la base de datos.")