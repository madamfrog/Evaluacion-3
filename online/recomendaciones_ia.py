import logging
import re
from typing import Any, Literal

from django.conf import settings
from django.db.models import Count, QuerySet

from online.models import Preguntas

# Configuración del logger para la app online

logger: logging.Logger = settings.LOGGER
class RecomendadorIA:
    def __init__(self) -> None:
        self.palabras_comunes = [
            'el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 
            'te', 'lo', 'le', 'su', 'por', 'con', 'para', 'al', 'del',
            'los', 'las', 'una', 'uno', 'como', 'pero', 'mi', 'ya', 'muy'
        ]
    
    def recomendar_respuestas_similares(self, nueva_pregunta: str) -> list[Any]:
        """
        Encuentra preguntas similares usando comparación simple de palabras
        """
        try:
            # Obtener todas las preguntas resueltas
            preguntas_resueltas: QuerySet[Preguntas] = Preguntas.objects.filter(
                respuesta__isnull=False
            ).distinct()
            
            if not preguntas_resueltas:
                return []
            
            # Limpiar y tokenizar la nueva pregunta
            palabras_nueva: list[str] = self._limpiar_y_tokenizar(nueva_pregunta)
            
            recomendaciones: list[Any] = []
            
            for pregunta in preguntas_resueltas:
                # Combinar título y pregunta para la comparación
                texto_pregunta: str = f"{pregunta.Titulo} {pregunta.Pregunta}"
                palabras_pregunta: list[str] = self._limpiar_y_tokenizar(texto_pregunta)
                
                # Calcular similitud simple (intersección de palabras)
                palabras_comunes: set[str] = set(palabras_nueva) & set(palabras_pregunta)
                lista_palabras_comunes: list[str] = [p for p in palabras_comunes if p not in self.palabras_comunes and len(p) > 3]
                
                if palabras_comunes:
                    # Calcular similitud más sofisticada
                    similitud: float | Literal[0] = self._calcular_similitud(palabras_nueva, palabras_pregunta, lista_palabras_comunes)
                    
                    if similitud > 0.15:  # Umbral mínimo de similitud
                        mejor_respuesta = pregunta.respuesta_set.first()
                        if mejor_respuesta:
                            recomendaciones.append({
                                'pregunta_similar': pregunta.Titulo,
                                'respuesta': mejor_respuesta.Respuesta[:150] + "..." if len(mejor_respuesta.Respuesta) > 150 else mejor_respuesta.Respuesta,
                                'similitud': round(similitud, 2),
                                'categoria': getattr(pregunta, 'categoria', 'general')
                            })
            
            # Ordenar por similitud y devolver máximo 3
            recomendaciones.sort(key=lambda x: x['similitud'], reverse=True)
            return recomendaciones[:3]
            
        except Exception as e:
            logger.error("Error en recomendaciones: %s", e)
            return []
    
    def _calcular_similitud(self, palabras1: list[str], palabras2: list[str], palabras_comunes: list[str]) -> float | Literal[0]:
        """Calcula similitud entre dos conjuntos de palabras"""
        if not palabras1 or not palabras2:
            return 0
        
        peso_palabras_comunes = len(palabras_comunes)
        peso_longitud = min(len(palabras1), len(palabras2)) / max(len(palabras1), len(palabras2))
        
        similitud = (peso_palabras_comunes * 0.7) + (peso_longitud * 0.3)
        return min(similitud / 5, 1.0)
    
    def _limpiar_y_tokenizar(self, texto: str) -> list[str]:
        """
        Limpia y tokeniza el texto para comparación
        """
        if not texto:
            return []
        
        texto_limpio = re.sub(r'[^\w\sáéíóúñ]', '', texto.lower()) # Convertir a minúsculas y eliminar caracteres

        palabras = [palabra for palabra in texto_limpio.split() # Eliminar palabras vacías
                    if palabra not in self.palabras_comunes and len(palabra) > 2]
        
        return palabras
    
    def obtener_preguntas_populares(self, limite: int = 5) -> list[Any]:
        """
        Obtiene las preguntas más populares/resueltas
        """
        try:
            preguntas_populares = Preguntas.objects.annotate(
                num_respuestas=Count('respuesta')
            ).filter(num_respuestas__gt=0).order_by('-num_respuestas')[:limite]
            
            return [
                {
                    'titulo': p.Titulo,
                    'respuestas': p.num_respuestas,
                    'categoria': getattr(p, 'categoria', 'general')
                }
                for p in preguntas_populares
            ]
        except Exception as e:
            logger.error("Error obteniendo preguntas populares: %s", e)
            return []

def obtener_recomendaciones_ia(nueva_pregunta: str) -> list[str]:
    recomendador = RecomendadorIA()
    return recomendador.recomendar_respuestas_similares(nueva_pregunta)