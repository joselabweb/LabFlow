import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
import logging

class TranscriptionHistory:
    def __init__(self, history_file: str = "nuevo_transcription_history.json", max_entries: int = 1000):
        self.history_file = history_file
        self.stats_file = "nuevo_usage_statistics.json" # Archivo de estadísticas separado
        self.max_entries = max_entries
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        """Asegura que los archivos de historial y estadísticas existan."""
        if not os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)
            except Exception as e:
                logging.error(f"No se pudo crear el archivo de historial {self.history_file}: {e}")

        if not os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
            except Exception as e:
                logging.error(f"No se pudo crear el archivo de estadísticas {self.stats_file}: {e}")

    def add_transcription(self, text: str, duration: float, used_gemini: bool = False, mode: str = "gemini_only") -> None:
        """Añade una nueva transcripción al historial."""
        try:
            entry = {
                'timestamp': datetime.now().isoformat(),
                'text': text,
                'duration': duration,
                'used_gemini': used_gemini,
                'mode': mode
            }
            
            with open(self.history_file, 'r+', encoding='utf-8') as f:
                history = json.load(f)
                history.insert(0, entry)
                
                if len(history) > self.max_entries:
                    history = history[:self.max_entries]
                
                f.seek(0)
                json.dump(history, f, ensure_ascii=False, indent=2)
                f.truncate()
            
        except Exception as e:
            logging.error(f"Error al añadir transcripción al historial: {e}")

    def get_recent_transcriptions(self, limit: int = 10) -> List[Dict]:
        """Obtiene las transcripciones más recientes."""
        try:
            if not os.path.exists(self.history_file):
                return []
                
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
                return history[:limit]
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logging.error(f"Error al leer el historial {self.history_file}: {e}")
            return []
        except Exception as e:
            logging.error(f"Error inesperado al leer el historial: {e}")
            return []

    def search_transcriptions(self, query: str) -> List[Dict]:
        """Busca transcripciones que contengan el texto especificado."""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
                return [entry for entry in history if query.lower() in entry['text'].lower()]
        except Exception as e:
            logging.error(f"Error al buscar en el historial: {e}")
            return []

    def get_statistics(self) -> Dict:
        """Calcula estadísticas a partir del historial de transcripciones."""
        default_stats = {
            'last_24h': {'total': 0, 'gemini': 0},
            'last_week': {'total': 0, 'gemini': 0},
            'last_month': {'total': 0, 'gemini': 0},
            'total_duration': 0,
            'avg_duration': 0,
            'total_gemini_requests': 0
        }
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
                
            if not history:
                return default_stats

            now = datetime.now()
            last_24h_limit = now - timedelta(hours=24)
            last_week_limit = now - timedelta(days=7)
            last_month_limit = now - timedelta(days=30)
            
            stats = {
                'last_24h': {'total': 0, 'gemini': 0},
                'last_week': {'total': 0, 'gemini': 0},
                'last_month': {'total': 0, 'gemini': 0},
                'total_duration': 0.0,
                'total_gemini_requests': 0
            }
            
            total_entries = len(history)
            
            for entry in history:
                try:
                    timestamp = datetime.fromisoformat(entry['timestamp'])
                    duration = float(entry.get('duration', 0.0))
                    used_gemini = entry.get('used_gemini', False)
                    
                    if timestamp >= last_24h_limit:
                        stats['last_24h']['total'] += 1
                        if used_gemini:
                            stats['last_24h']['gemini'] += 1
                            
                    if timestamp >= last_week_limit:
                        stats['last_week']['total'] += 1
                        if used_gemini:
                            stats['last_week']['gemini'] += 1

                    if timestamp >= last_month_limit:
                        stats['last_month']['total'] += 1
                        if used_gemini:
                            stats['last_month']['gemini'] += 1
                    
                    stats['total_duration'] += duration
                    if used_gemini:
                        stats['total_gemini_requests'] += 1
                except (ValueError, TypeError) as e:
                    logging.warning(f"Saltando entrada de historial mal formada: {entry}. Error: {e}")
                    total_entries -= 1 # No contar entradas corruptas para el promedio
            
            if total_entries > 0:
                stats['avg_duration'] = stats['total_duration'] / total_entries
            else:
                stats['avg_duration'] = 0.0
            
            return stats
            
        except Exception as e:
            logging.error(f"Error al obtener estadísticas: {e}")
            return default_stats