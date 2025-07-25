import keyboard
import pyaudio
import wave
import tempfile
import os
import pyperclip
from pynput.mouse import Controller
import time
import threading
import tkinter as tk
from tkinter import ttk
import sys
import re
from nuevo_transcription_history import TranscriptionHistory
from nuevo_text_enhancer import TextEnhancer
from datetime import datetime, timedelta
import json
import customtkinter as ctk
import logging
import webbrowser
import traceback

# Configurar el sistema de logging
def setup_logging():
    # Obtener la ruta del directorio de la aplicación
    if getattr(sys, 'frozen', False):
        # Si estamos en un ejecutable
        app_dir = os.path.dirname(sys.executable)
    else:
        # Si estamos en desarrollo
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Crear directorio de logs si no existe
    log_dir = os.path.join(app_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configurar el archivo de log
    log_file = os.path.join(log_dir, 'wisprflow_soft_nuevo.log')
    
    # Configurar el formato del logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # También mostrar en consola
        ]
    )
    
    # Log inicial
    logging.info('Iniciando WisprFlow Soft (Nuevo Script)')
    logging.info(f'Directorio de la aplicación: {app_dir}')
    logging.info(f'Archivo de log: {log_file}')

# Configurar el manejador de excepciones global
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logging.error("Excepción no manejada:", exc_info=(exc_type, exc_value, exc_traceback))

# Configurar el manejador de excepciones
sys.excepthook = handle_exception

# Iniciar el sistema de logging
setup_logging()

# Configuración de la grabación
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent, history, text_enhancer, app):
        super().__init__(parent)
        self.parent = parent
        self.history = history
        self.text_enhancer = text_enhancer
        self.app = app
        self.gemini_models = [
            "gemini-2.5-flash",
            "gemini-2.5-flash-preview-04-17",
            "gemini-2.5-flash-lite-preview-06-17"
        ]
        
        self.title("Wispr Flow Soft - Configuración")
        self.geometry("1000x700")
        
        self.update_idletasks()
        width = 1000
        height = 700
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # Guardar colores por defecto para poder revertirlos
        self._default_selected_color = ctk.ThemeManager.theme["CTkSegmentedButton"]["selected_color"]
        self._default_selected_hover_color = ctk.ThemeManager.theme["CTkSegmentedButton"]["selected_hover_color"]
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.tabview = ctk.CTkTabview(self, command=self.on_tab_change)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tabview.add("API")
        self.tabview.add("Historial")
        self.tabview.add("Estadísticas")
        self.tabview.add("Configuración")
        self.tabview.add("Modelo Gemini")
        self.tabview.add("Donar")
        
        # --- Custom color for the "Donar" tab button ---
        # This ensures the tab button itself has a unique color, even when not selected.
        # We use a slightly darker yellow for the non-selected state.
        donate_fg_color = "#B8860B"  # DarkGoldenRod
        donate_hover_color = "#DAA520" # GoldenRod
        donate_text_color = "#FFFFFF" # White text for better contrast

        try:
            # Access the internal button dictionary to configure a specific tab button
            donate_button = self.tabview._segmented_button._buttons_dict["Donar"]
            donate_button.configure(
                fg_color=donate_fg_color,
                hover_color=donate_hover_color,
                text_color=donate_text_color
            )
        except (AttributeError, KeyError) as e:
            logging.warning(f"Could not apply custom color to 'Donar' tab: {e}")
        
        self.setup_api_tab()
        self.setup_history_tab()
        self.setup_stats_tab()
        self.setup_config_tab()
        self.setup_model_tab()
        self.setup_donate_tab()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.transient(parent)
        self.grab_set()
        
        self.update()
        self.deiconify()
        self.lift()
        self.focus_force()

    def on_tab_change(self):
        selected_tab = self.tabview.get()
        
        # Un color amarillo/dorado que resalta
        donate_color = "#FFD700"  # Gold, for when selected
        donate_hover_color = "#FFC300"

        if selected_tab == "Donar":
            self.tabview.configure(
                segmented_button_selected_color=donate_color,
                segmented_button_selected_hover_color=donate_hover_color
            )
        else:
            # Revertir a los colores por defecto del tema
            self.tabview.configure(
                segmented_button_selected_color=self._default_selected_color,
                segmented_button_selected_hover_color=self._default_selected_hover_color
            )

    def setup_api_tab(self):
        tab = self.tabview.tab("API")
        
        title = ctk.CTkLabel(tab, text="Configuración de la API de Gemini", font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(pady=(10, 20))
        
        api_frame = ctk.CTkFrame(tab)
        api_frame.pack(fill="x", padx=10, pady=10)
        
        label = ctk.CTkLabel(api_frame, text="API Key:", width=100)
        label.pack(side="left", padx=5)
        
        api_entry = ctk.CTkEntry(api_frame, width=400, show="*")
        api_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        if self.text_enhancer.api_key:
            api_entry.insert(0, self.text_enhancer.api_key)

        def save_api_key():
            api_key = api_entry.get().strip()
            if self.text_enhancer.set_api_key(api_key):
                from customtkinter.windows.widgets.ctk_messagebox import CTkMessagebox
                CTkMessagebox(title="Éxito", message="API Key guardada y configurada correctamente.", icon="check", parent=self)
            else:
                from customtkinter.windows.widgets.ctk_messagebox import CTkMessagebox
                CTkMessagebox(title="Error", message="Error al configurar la API. Verifica la clave.", icon="cancel", parent=self)
        
        save_button = ctk.CTkButton(tab, text="Guardar y Activar API", command=save_api_key)
        save_button.pack(pady=20)
        
    def setup_history_tab(self):
        tab = self.tabview.tab("Historial")
        
        title = ctk.CTkLabel(tab, text="Historial de Transcripciones", font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(pady=(10, 20))
        
        frame = ctk.CTkScrollableFrame(tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        history_entries = self.history.get_recent_transcriptions(10)
        
        if not history_entries:
            ctk.CTkLabel(frame, text="No hay transcripciones en el historial.").pack(pady=10)
        else:
            for entry in history_entries:
                entry_frame = ctk.CTkFrame(frame)
                entry_frame.pack(fill="x", pady=5, padx=5)
                
                timestamp = datetime.fromisoformat(entry['timestamp'])
                formatted_time = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                
                info_frame = ctk.CTkFrame(entry_frame, fg_color="transparent")
                info_frame.pack(fill="x", padx=10, pady=(10, 0))
                
                ctk.CTkLabel(info_frame, text=formatted_time, text_color="#4EC9B0").pack(side="left")
                ctk.CTkLabel(info_frame, text=f"Duración: {entry['duration']:.2f}s", text_color="#9CDCFE").pack(side="left", padx=(10, 0))
                
                mode_text = "Modo Gemini"
                if entry.get('used_gemini', False):
                    mode_text += " + Mejoras"
                ctk.CTkLabel(info_frame, text=mode_text, text_color="#CE9178").pack(side="left", padx=(10, 0))
                
                text_frame = ctk.CTkFrame(entry_frame, fg_color="transparent")
                text_frame.pack(fill="x", padx=10, pady=(5, 10))
                
                def create_copy_button(text):
                    def copy_text():
                        pyperclip.copy(text)
                        button.configure(text="✓", fg_color="#4CAF50")
                        button.after(1000, lambda: button.configure(text="📋", fg_color="#0E639C"))
                    return copy_text
                
                button = ctk.CTkButton(text_frame, text="📋", width=30, command=create_copy_button(entry['text']), fg_color="#0E639C", hover_color="#1177BB")
                button.pack(side="left", padx=(0, 10))
                
                text_label = ctk.CTkLabel(text_frame, text=entry['text'], text_color="#DCDCAA", justify="left", wraplength=700)
                text_label.pack(side="left", fill="x", expand=True)
                
    def setup_stats_tab(self):
        tab = self.tabview.tab("Estadísticas")
        
        title = ctk.CTkLabel(tab, text="Estadísticas de Uso", font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(pady=(10, 20))
        
        stats = self.history.get_statistics()
        frame = ctk.CTkScrollableFrame(tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        def create_stat_section(title, data):
            section = ctk.CTkFrame(frame)
            section.pack(fill="x", pady=5, padx=5)
            ctk.CTkLabel(section, text=title, font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
            for key, value in data.items():
                row = ctk.CTkFrame(section, fg_color="transparent")
                row.pack(fill="x", padx=10, pady=2)
                ctk.CTkLabel(row, text=f"{key}:").pack(side="left")
                ctk.CTkLabel(row, text=str(value)).pack(side="right")
        
        create_stat_section("Últimas 24 horas", {"Total transcripciones": stats['last_24h']['total'], "Con mejoras": stats['last_24h']['gemini']})
        create_stat_section("Última semana", {"Total transcripciones": stats['last_week']['total'], "Con mejoras": stats['last_week']['gemini']})
        create_stat_section("Último mes", {"Total transcripciones": stats['last_month']['total'], "Con mejoras": stats['last_month']['gemini']})
        create_stat_section("Totales", {"Peticiones a Gemini": stats['total_gemini_requests'], "Duración promedio": f"{stats['avg_duration']:.2f}s"})

    def setup_config_tab(self):
        tab = self.tabview.tab("Configuración")
        
        title = ctk.CTkLabel(tab, text="Configuración del Prompt de Mejora", font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(pady=(10, 20))
        
        prompt_frame = ctk.CTkFrame(tab)
        prompt_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        prompt_area = ctk.CTkTextbox(prompt_frame, font=("Consolas", 12))
        prompt_area.pack(fill="both", expand=True, padx=10, pady=10)
        
        current_prompt = self.text_enhancer.get_current_prompt()
        prompt_area.insert("1.0", current_prompt)
        
        def save_prompt():
            new_prompt = prompt_area.get("1.0", "end-1c").strip()
            if self.text_enhancer.update_prompt(new_prompt):
                from customtkinter.windows.widgets.ctk_messagebox import CTkMessagebox
                CTkMessagebox(title="Éxito", message="Prompt actualizado correctamente", parent=self)
            else:
                from customtkinter.windows.widgets.ctk_messagebox import CTkMessagebox
                CTkMessagebox(title="Error", message="No se pudo actualizar el prompt", icon="cancel", parent=self)
        
        save_button = ctk.CTkButton(tab, text="Guardar Prompt", command=save_prompt)
        save_button.pack(pady=10)

    def setup_model_tab(self):
        tab = self.tabview.tab("Modelo Gemini")
        title = ctk.CTkLabel(tab, text="Selecciona el modelo de Gemini", font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(pady=(10, 20))
        
        model_var = ctk.StringVar(value=self.text_enhancer.get_model())
        combobox = ctk.CTkComboBox(tab, values=self.gemini_models, variable=model_var, width=400)
        combobox.pack(pady=20)
        
        def save_model():
            nuevo_modelo = model_var.get()
            self.text_enhancer.set_model(nuevo_modelo)
            save_button.configure(text="✓ Guardado", fg_color="#4CAF50")
            save_button.after(1000, lambda: save_button.configure(text="Guardar modelo", fg_color="#1f6aa5"))
        
        save_button = ctk.CTkButton(tab, text="Guardar modelo", command=save_model, fg_color="#1f6aa5")
        save_button.pack(pady=10)

    def open_link(self, url: str):
        """Abre un enlace en el navegador por defecto."""
        webbrowser.open_new(url)

    def setup_donate_tab(self):
        """Configura la pestaña de Donación."""
        tab = self.tabview.tab("Donar")
        
        # Centrar el contenido en la pestaña
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        
        content_frame = ctk.CTkFrame(tab, fg_color="transparent")
        content_frame.grid(row=0, column=0, sticky="nsew")

        # Texto de agradecimiento
        text_label = ctk.CTkLabel(
            content_frame,
            text="Si te ha gustado esta aplicación, puedes hacer una donación.",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        text_label.pack(pady=(20, 10), padx=20)

        # Enlace clicable
        link_url = "https://buymeacoffee.com/joselabweb"
        link_font = ctk.CTkFont(size=14, underline=True)
        link_label = ctk.CTkLabel(
            content_frame, text=link_url, font=link_font, text_color="#60A5FA"
        )
        link_label.pack(pady=20)

        # Hacerlo clicable y cambiar cursor
        link_label.bind("<Button-1>", lambda e: self.open_link(link_url))
        link_label.bind("<Enter>", lambda e: link_label.configure(cursor="hand2"))
        link_label.bind("<Leave>", lambda e: link_label.configure(cursor=""))

    def on_closing(self):
        self.grab_release()
        self.destroy()

class WisprApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wispr Flow Soft")
        
        self.history = TranscriptionHistory("nuevo_transcription_history.json")
        self.text_enhancer = TextEnhancer("nuevo_config.json")
        
        self.root.attributes('-alpha', 0.9)
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 100
        window_height = 30
        x = (screen_width - window_width) // 2
        y = screen_height - window_height - 40
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.main_frame = ctk.CTkFrame(self.root, fg_color='#2C2C2C', corner_radius=20)
        self.main_frame.pack(fill='both', expand=True)
        
        self.status_frame = ctk.CTkFrame(self.main_frame, fg_color='#2C2C2C')
        self.status_frame.pack(fill='both', expand=True)
        
        self.use_enhancer = ctk.BooleanVar(value=self.text_enhancer.enabled)
        self.enhancer_check = ctk.CTkCheckBox(
            self.status_frame, text="", variable=self.use_enhancer,
            width=20, height=20, fg_color='#2C2C2C', hover_color='#2C2C2C',
            command=self.toggle_text_enhancer
        )
        self.enhancer_check.pack(side='left', padx=2)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame, text="•", font=("Arial", 20),
            text_color='#FFFFFF', fg_color='#2C2C2C'
        )
        self.status_label.pack(side='left', pady=2)
        
        self.mode_label = ctk.CTkLabel(
            self.status_frame, text="G", font=("Arial", 10),
            text_color='#4EC9B0', fg_color='#2C2C2C'
        )
        self.mode_label.pack(side='right', padx=5)
        
        self.grabando = False
        self.frames = []
        self.ultima_pulsacion = 0
        self.DEBOUNCE_TIME = 0.5
        self.animacion_activa = False
        self.estado_actual = "inactivo"
        
        keyboard.add_hotkey('ctrl+less', self.toggle_grabacion)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.animar_puntos()
        self.setup_context_menu()
        self.settings_window = None

        # Variables y eventos para arrastrar la ventana
        self._offset_x = 0
        self._offset_y = 0
        for widget in [self.main_frame, self.status_frame, self.status_label, self.enhancer_check, self.mode_label]:
            widget.bind("<ButtonPress-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.do_drag)

    def start_drag(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def do_drag(self, event):
        x = self.root.winfo_pointerx() - self._offset_x
        y = self.root.winfo_pointery() - self._offset_y
        self.root.geometry(f"+{x}+{y}")

    def toggle_text_enhancer(self):
        self.text_enhancer.set_enabled(self.use_enhancer.get())

    def animar_puntos(self):
        if not hasattr(self, 'root') or not self.root.winfo_exists():
            return
        try:
            if self.animacion_activa:
                if self.estado_actual == "grabando":
                    puntos = "•" * (int(time.time() * 2) % 4)
                    self.status_label.configure(text=puntos, text_color='#FF0000')
                elif self.estado_actual == "transcribiendo":
                    puntos = "•" * (int(time.time() * 1.5) % 4)
                    self.status_label.configure(text=puntos, text_color='#FFD700')
            else:
                self.status_label.configure(text="•", text_color='#FFFFFF')
            if self.root.winfo_exists():
                self.root.after(100, self.animar_puntos)
        except Exception as e:
            logging.warning(f"Error en animar_puntos: {e}")

    def actualizar_estado(self, estado, activar_animacion=True):
        if not hasattr(self, 'root') or not self.root.winfo_exists():
            return
        try:
            self.animacion_activa = activar_animacion
            self.estado_actual = estado
            if not activar_animacion:
                self.status_label.configure(text="•", text_color='#FFFFFF')
        except Exception as e:
            logging.warning(f"Error en actualizar_estado: {e}")

    def grabar_audio(self):
        logging.info("Iniciando grabación de audio")
        p = pyaudio.PyAudio()
        stream = None
        try:
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                          input=True, frames_per_buffer=CHUNK)
            self.actualizar_estado("grabando", True)
            self.frames = []
            logging.info("Iniciando captura de frames de audio")
            while self.grabando:
                data = stream.read(CHUNK, exception_on_overflow=False)
                self.frames.append(data)
        except Exception as e:
            logging.error(f"Error durante la grabación: {e}")
            return None
        finally:
            if stream:
                stream.stop_stream()
                stream.close()
            p.terminate()
            logging.info("Recursos de PyAudio liberados.")
        
        if not self.frames:
            logging.warning("No se capturaron frames de audio.")
            return None
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                wf = wave.open(temp_file.name, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(self.frames))
                wf.close()
                logging.info(f"Audio guardado en: {temp_file.name}")
                return temp_file.name
        except Exception as e:
            logging.error(f"Error al guardar archivo WAV: {e}")
            return None

    def pegar_texto(self, texto):
        if texto:
            pyperclip.copy(texto)
            keyboard.send('ctrl+v')
            self.actualizar_estado("inactivo", False)

    def toggle_grabacion(self):
        tiempo_actual = time.time()
        if tiempo_actual - self.ultima_pulsacion < self.DEBOUNCE_TIME:
            return
        self.ultima_pulsacion = tiempo_actual
        
        if not self.grabando:
            logging.info("Iniciando grabación...")
            self.grabando = True
            threading.Thread(target=self.procesar_grabacion, daemon=True).start()
        else:
            logging.info("Deteniendo grabación...")
            self.grabando = False
            self.actualizar_estado("transcribiendo", True)

    def procesar_grabacion(self):
        if not self.text_enhancer.is_configured:
            logging.error("API de Gemini no configurada. Abortando transcripción.")
            self.root.after(0, self.show_api_warning_window)
            self.actualizar_estado("inactivo", False)
            return

        tiempo_inicio = time.time()
        audio_file = self.grabar_audio()
        
        if audio_file:
            texto_final = ""
            used_gemini = False
            try:
                texto_transcrito = self.text_enhancer.transcribe_audio(audio_file)
                used_gemini = True
                
                if self.use_enhancer.get():
                    logging.info("Aplicando mejoras de texto...")
                    texto_final = self.text_enhancer.enhance_text(texto_transcrito)
                else:
                    texto_final = texto_transcrito
                    
            except Exception as e:
                logging.error(f"Error en la transcripción con Gemini: {e}")
                texto_final = "Error en la transcripción. Verifique su API Key y conexión."
            
            duracion = time.time() - tiempo_inicio
            self.history.add_transcription(texto_final, duracion, used_gemini, "gemini_only")
            self.root.after(0, self.pegar_texto, texto_final)
            
            try:
                os.unlink(audio_file)
                logging.info(f"Archivo temporal {audio_file} eliminado.")
            except Exception as e:
                logging.error(f"Error al eliminar archivo temporal: {e}")
        else:
            logging.warning("No se generó archivo de audio para transcribir.")
        
        self.actualizar_estado("inactivo", False)

    def show_error_message(self, message):
        from customtkinter.windows.widgets.ctk_messagebox import CTkMessagebox
        CTkMessagebox(title="Error", message=message, icon="cancel")

    def show_api_warning_window(self):
        if hasattr(self, 'api_warning_window') and self.api_warning_window.winfo_exists():
            self.api_warning_window.lift()
            self.api_warning_window.focus_force()
            return

        self.api_warning_window = ctk.CTkToplevel(self.root)
        self.api_warning_window.title("Advertencia")
        self.api_warning_window.attributes('-topmost', True)
        self.api_warning_window.configure(fg_color="#2C2C2C")
        self.api_warning_window.protocol("WM_DELETE_WINDOW", self.api_warning_window.destroy)
        self.api_warning_window.resizable(False, False)

        WIN_WIDTH = 400

        label = ctk.CTkLabel(
            self.api_warning_window,
            text="Tienes que poner la API para poder grabar. Cierra esta ventana, haz clic derecho en el programa y selecciona 'Configuración' para pegar tu clave API.",
            wraplength=WIN_WIDTH - 20,
            fg_color="transparent",
            text_color="#FFCC00",
            font=("Arial", 10),
            justify="center"
        )
        label.pack(padx=10, pady=10, fill="x", expand=True)

        self.api_warning_window.update_idletasks()

        win_height = self.api_warning_window.winfo_height()
        
        main_win_x = self.root.winfo_x()
        main_win_y = self.root.winfo_y()
        main_win_width = self.root.winfo_width()
        
        x = main_win_x + (main_win_width - WIN_WIDTH) // 2
        y = main_win_y - win_height

        self.api_warning_window.geometry(f'{WIN_WIDTH}x{win_height}+{x}+{y}')
        self.api_warning_window.grab_set()

    def on_closing(self):
        try:
            logging.info("Cerrando la aplicación...")
            self.grabando = False
            self.animacion_activa = False
            keyboard.remove_hotkey('ctrl+less')
            
            if self.settings_window and self.settings_window.winfo_exists():
                self.settings_window.destroy()
            
            self.text_enhancer._save_config()
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            logging.error(f"Error durante el cierre: {e}")
        finally:
            os._exit(0)

    def setup_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Configuración", command=self.show_settings)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Salir", command=self.on_closing)
        
        for widget in [self.root, self.main_frame, self.status_frame, self.status_label, self.enhancer_check, self.mode_label]:
            widget.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def show_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self.root, self.history, self.text_enhancer, self)
        self.settings_window.deiconify()
        self.settings_window.lift()
        self.settings_window.focus_force()

def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    app = WisprApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()