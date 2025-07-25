import os
import json
import google.generativeai as genai
from typing import Optional
from datetime import datetime
import base64
import logging

class TextEnhancer:
    def __init__(self, config_file="nuevo_config.json"):
        self.config_file = config_file
        self.api_key = None
        self.is_configured = False
        self.enabled = True
        self.default_prompt = """
        Mejora la puntuación y el formato del siguiente texto en español:
        1. Añade signos de puntuación donde falten
        2. Añade saltos de línea naturales
        3. Corrige la capitalización
        4. Mantén el significado original
        5. No añadas contenido nuevo
        6. Dame directamente el texto mejorado sin ningún comentario adicional
        7. NO añadas un comentario inicial tipo "Aquí tienes el texto mejorado, siguiendo tus indicaciones:"
        
        Texto a mejorar:
        """
        self.model = "gemini-2.5-flash-lite-preview-06-17"
        self._load_config()

    def _load_config(self):
        """Carga la configuración desde el archivo."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Clave de API es la única que se obtiene aquí
                    self.api_key = config.get('gemini_api_key', None)
                    self.enabled = config.get('enable_text_enhancement', True)
                    self.prompt = config.get('prompt', self.default_prompt)
                    self.model = config.get('gemini_model', self.model)
                    if self.api_key:
                        self._configure_api()
            else:
                # Crear archivo de configuración por defecto si no existe
                self.prompt = self.default_prompt
                self._save_config()
        except json.JSONDecodeError:
            logging.error(f"Error al decodificar JSON de {self.config_file}. Creando uno nuevo.")
            self.prompt = self.default_prompt
            self._save_config()
        except Exception as e:
            logging.error(f"Error al cargar la configuración: {e}")
            self.prompt = self.default_prompt

    def _save_config(self):
        """Guarda la configuración actual en el archivo."""
        try:
            config = {
                'gemini_api_key': self.api_key or '',
                'enable_text_enhancement': self.enabled,
                'prompt': self.prompt,
                'gemini_model': self.model
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logging.error(f"Error al guardar la configuración: {e}")

    def _configure_api(self):
        """Configura la API de Gemini con la clave cargada."""
        if not self.api_key:
            self.is_configured = False
            return
        try:
            genai.configure(api_key=self.api_key)
            # Verificar que la configuración funciona listando modelos
            genai.list_models()
            self.is_configured = True
            logging.info("API de Gemini configurada correctamente.")
        except Exception as e:
            logging.error(f"Error al configurar la API de Gemini: {e}")
            self.is_configured = False

    def enhance_text(self, text: str) -> str:
        """Mejora el texto usando la API de Gemini."""
        if not self.enabled or not self.is_configured or not text.strip():
            return text
        try:
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(self.prompt + text)
            enhanced_text = response.text.strip()
            return enhanced_text if enhanced_text else text
        except Exception as e:
            logging.error(f"Error al mejorar el texto: {e}")
            return text

    def set_api_key(self, api_key: str) -> bool:
        """Establece una nueva API key, la configura y la guarda."""
        self.api_key = api_key
        self._configure_api()
        self._save_config()
        return self.is_configured

    def set_enabled(self, enabled: bool):
        """Activa o desactiva la mejora de texto y guarda el estado."""
        self.enabled = enabled
        self._save_config()

    def get_current_prompt(self) -> str:
        return self.prompt

    def update_prompt(self, new_prompt: str) -> bool:
        """Actualiza el prompt de Gemini y lo guarda."""
        try:
            self.prompt = new_prompt
            self._save_config()
            return True
        except Exception as e:
            logging.error(f"Error al actualizar el prompt: {e}")
            return False

    def set_model(self, model: str):
        self.model = model
        self._save_config()

    def get_model(self) -> str:
        return self.model

    def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe un archivo de audio usando la API de Gemini."""
        if not self.is_configured:
            raise Exception("API de Gemini no configurada. Añada su API Key en Configuración.")

        try:
            logging.info(f"Transcribiendo archivo de audio: {audio_file_path}")
            
            # Subir el archivo de audio a la API de Gemini
            audio_file = genai.upload_file(path=audio_file_path)
            logging.info(f"Archivo subido: {audio_file.display_name}")

            # Crear el modelo generativo
            model = genai.GenerativeModel(model_name=self.model)

            # Prompt para la transcripción
            prompt = """
            Por favor, transcribe el siguiente audio al español.
            Quita expresiones como "uhm", "ah" o similares que no sean palabras sino muletillas.
            Mantén la puntuación natural. No añadas contenido que no esté en el audio.
            Devuelve solo el texto transcrito.
            """

            # Generar el contenido
            response = model.generate_content([prompt, audio_file])
            
            if not response or not response.text:
                raise Exception("La API de Gemini no devolvió una respuesta válida.")
            
            texto_transcrito = response.text.strip()
            logging.info("Transcripción completada exitosamente.")
            
            # Limpiar el archivo subido de la API de Gemini
            try:
                genai.delete_file(name=audio_file.name)
                logging.info(f"Archivo {audio_file.name} eliminado de la API.")
            except Exception as e:
                logging.error(f"No se pudo eliminar el archivo de la API: {e}")
            
            return texto_transcrito

        except Exception as e:
            logging.error(f"Error detallado en la transcripción con Gemini: {e}")
            raise Exception(f"Error en la transcripción con Gemini: {e}")