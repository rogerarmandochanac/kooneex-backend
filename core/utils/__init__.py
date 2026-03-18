# utils.py - FUNCIONES OPTIMIZADAS
import math
from functools import lru_cache
from django.core.cache import cache

@lru_cache(maxsize=128)
def calcular_distancia(lat1, lon1, lat2, lon2):
    """Cálculo de distancia con caché para ubicaciones frecuentes"""
    if lat1 == lat2 and lon1 == lon2:
        return 0.0
    
    # Fórmula de Haversine optimizada
    R = 6371.0  # Radio de la Tierra en km
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def obtener_mototaxis_cercanos(lat, lon, radio_km=5):
    """Función optimizada para obtener mototaxis cercanos"""
    cache_key = f"mototaxis_cercanos_{lat:.4f}_{lon:.4f}_{radio_km}"
    resultado = cache.get(cache_key)
    
    if resultado is None:
        # Usar geodjango si está disponible, o cálculo manual optimizado
        from django.db import connection
        
        # SQL directo para mejor rendimiento
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, placa, latitud, longitud, 
                       (6371 * acos(
                           cos(radians(%s)) * cos(radians(latitud)) * 
                           cos(radians(longitud) - radians(%s)) + 
                           sin(radians(%s)) * sin(radians(latitud))
                       )) as distancia
                FROM app_mototaxi 
                WHERE disponible = TRUE 
                  AND latitud IS NOT NULL 
                  AND longitud IS NOT NULL
                HAVING distancia <= %s
                ORDER BY distancia
                LIMIT 20
            """, [lat, lon, lat, radio_km])
            
            mototaxis = cursor.fetchall()
            resultado = [
                {
                    'id': row[0],
                    'placa': row[1],
                    'latitud': row[2],
                    'longitud': row[3],
                    'distancia_km': round(row[4], 2)
                }
                for row in mototaxis
            ]
        
        # Cachear por 30 segundos
        cache.set(cache_key, resultado, 30)
    
    return resultado

def construir_url_imagen(request, image_field):
    if image_field:
        url = image_field.url
        return request.build_absolute_uri(url) if request else url
    return None