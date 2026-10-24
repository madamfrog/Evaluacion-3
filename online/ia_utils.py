import logging
from openai import OpenAI
from django.conf import settings
from django.core.cache import cache

# Configuración del logger para la app online
logger = logging.getLogger(__name__)

class AsistenteIA:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY

    def _client(self):
        if not self.api_key:
            raise RuntimeError("La variable de entorno OPENAI_API_KEY no está configurada.")
        return OpenAI(api_key=self.api_key)
    
    def generar_respuesta_automatica(self, pregunta, historial_contexto=""):
        """
        Genera una respuesta automática usando IA con caché para evitar llamadas repetidas
        """
        pregunta_key = pregunta.strip().lower()
        cache_key = f"ia_respuesta_{hash(pregunta_key)}"
        
        respuesta_cacheada = cache.get(cache_key)
        if respuesta_cacheada:
            logger.info("[CACHÉ HIT] Usando respuesta guardada para: '%s...'", pregunta[:30])
            return respuesta_cacheada

        try:
            prompt = f"""
            Eres un asistente técnico especializado en videojuegos y hardware gaming.
            
            Contexto del historial: {historial_contexto}
            
            Pregunta del usuario: {pregunta}
            
            Por favor, proporciona una respuesta útil, técnica pero comprensible.
            Si necesitas más información, pídela amablemente.
            Mantén un tono profesional pero cercano.
            
            Respuesta:
            """
            
            response = self._client().chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto técnico en videojuegos y hardware gaming."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            resultado = (response.choices[0].message.content or "").strip()
            
            cache.set(cache_key, resultado, 900)
            
            return resultado
            
        except Exception as e:
            logger.error("[Error interno de OpenAI - generar_respuesta]: %s", e)
            return "Lo sentimos, el asistente virtual no se encuentra disponible temporalmente. Por favor, intenta realizar tu consulta más tarde."
    
    def clasificar_pregunta(self, pregunta):
        """
        Clasifica la pregunta en categorías con caché para optimizar llamadas
        """
        categorias = [
            "hardware", "software", "conexion", "cuenta", 
            "pago", "rendimiento", "otros"
        ]
        
        pregunta_key = pregunta.strip().lower()
        cache_key = f"ia_clasificacion_{hash(pregunta_key)}"
        
        categoria_cacheada = cache.get(cache_key)
        if categoria_cacheada:
            return categoria_cacheada

        try:
            prompt = f"""
            Clasifica la siguiente pregunta del usuario en una de estas categorías: {', '.join(categorias)}
            
            Pregunta: {pregunta}
            
            Responde solo con la categoría más apropiada.
            """
            
            response = self._client().chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.3
            )
            
            categoria = (response.choices[0].message.content or "").strip().lower()
            resultado_final = categoria if categoria in categorias else "otros"
            
            cache.set(cache_key, resultado_final, 3600)
            
            return resultado_final
            
        except Exception as e:
            logger.error("[Error interno de OpenAI - clasificar_pregunta]: %s", e)
            return "otros"