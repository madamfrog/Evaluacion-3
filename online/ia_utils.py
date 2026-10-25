import logging

from django.core.cache import cache
from openai import OpenAI, OpenAIError

# Configuración del logger para la app online
logger = logging.getLogger(__name__)


class AsistenteIA:
    def __init__(self) -> None:
        self.MODEL = "llama3.1:8b"

    # FELIPE: NO ES NECESARIO LA API KEY, PORQUE LA IA ES LOCAL
    def _client(self) -> OpenAI:
        return OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

    def generar_respuesta_automatica(
        self, pregunta: str, historial_contexto: str = ""
    ) -> str:
        """
        Genera una respuesta automática usando IA con caché para evitar llamadas repetidas
        """
        pregunta_key = pregunta.strip().lower()
        cache_key = f"ia_respuesta_{hash(pregunta_key)}"

        respuesta_cacheada = cache.get(cache_key)
        if respuesta_cacheada:
            logger.info(
                "[CACHÉ HIT] Usando respuesta guardada para: '%s...'", pregunta[:30]
            )
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
                model=self.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto técnico en videojuegos y hardware gaming.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.7,
            )

            resultado = (response.choices[0].message.content or "").strip()

            cache.set(cache_key, resultado, 900)

            return resultado

        except OpenAIError as e:
            logger.error(f"[Error interno de OpenAI - generar_respuesta]: {e}")
            return "Lo sentimos, el asistente virtual no se encuentra disponible temporalmente. Por favor, intenta realizar tu consulta más tarde."

    def clasificar_pregunta(self, pregunta: str) -> str:
        """
        Clasifica la pregunta en categorías con caché para optimizar llamadas
        """
        categorias: list[str] = [
            "hardware",
            "software",
            "conexion",
            "cuenta",
            "pago",
            "rendimiento",
            "otros",
        ]

        pregunta_key: str = pregunta.strip().lower()
        cache_key: str = f"ia_clasificacion_{hash(pregunta_key)}"

        categoria_cacheada: str = cache.get(cache_key)

        if categoria_cacheada:
            return categoria_cacheada

        try:
            prompt: str = f"""
            Clasifica la siguiente pregunta del usuario en una de estas categorías: {", ".join(categorias)}
            
            Pregunta: {pregunta}
            
            Responde solo con la categoría más apropiada.
            """

            response = self._client().chat.completions.create(
                model=self.MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.3,
            )

            categoria: str = (response.choices[0].message.content or "").strip().lower()
            resultado_final: str

            if categoria in categorias:
                resultado_final = categoria
            else:
                resultado_final = "otros"

            cache.set(cache_key, resultado_final, 3600)

            return resultado_final

        except OpenAIError as e:
            logger.error(f"[Error interno de OpenAI - clasificar_pregunta]: {e}")
            return "otros"
