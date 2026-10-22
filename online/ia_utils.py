from openai import OpenAI
from django.conf import settings

class AsistenteIA:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY

    def _client(self):
        if not self.api_key:
            raise RuntimeError("La variable de entorno OPENAI_API_KEY no está configurada.")
        return OpenAI(api_key=self.api_key)
    
    def generar_respuesta_automatica(self, pregunta, historial_contexto=""):
        """
        Genera una respuesta automática usando IA
        """
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
            
            return (response.choices[0].message.content or "").strip()
            
        except Exception as e:
            return f"Lo siento, no puedo generar una respuesta en este momento. Error: {e}"
    
    def clasificar_pregunta(self, pregunta):
        """
        Clasifica la pregunta en categorías
        """
        categorias = [
            "hardware", "software", "conexion", "cuenta", 
            "pago", "rendimiento", "otros"
        ]
        
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
            return categoria if categoria in categorias else "otros"
            
        except Exception as e:
            return "otros"