"""
Interfaz gráfica mejorada de Aurora - Diseño futurista premium
Modos: Chat y Voz con conversación continua
Versión con Widget Flotante Integrado
PARTE 1/3: Imports, Workers, Helpers y Clases Base
"""
import sys
import threading
import logging
import re
import time

from PySide6.QtCore import Property
from PySide6.QtGui import QPixmap
from src.floating_assistant import FloatingVoiceWidget
from PySide6.QtCore import Qt, QPropertyAnimation, QThread, Signal, QTimer, QEasingCurve, QPoint
from PySide6.QtGui import QFont, QCursor, QPainter, QColor, QLinearGradient, QRadialGradient, QClipboard
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QTextEdit
)

from config.settings import WINDOW_TITLE
from src.main import escuchar, procesar_comando, stop_tts, tts_is_playing
from src.cerebro_ia import generar_respuesta
from gtts import gTTS
import os
import platform

# Configurar logging
logger = logging.getLogger(__name__)

# Paleta de colores futurista
COLORS = {
    'background': '#0a0e27',
    'surface': '#1a1f3a',
    'surface_light': '#252b48',
    'cyan': '#00d9ff',
    'magenta': '#bf00ff',
    'pink': '#ff0080',
    'navy': '#1a237e',
    'text': '#e0e6ff',
    'text_dim': '#8b93b8',
}

# Variables globales para controlar la reproducción de voz
voz_activa = False
detener_voz_flag = False


def limpiar_texto_para_voz(texto):
    """Limpia el texto removiendo markdown y emojis para síntesis de voz"""
    texto = re.sub(r'\*\*(.+?)\*\*', r'\1', texto)
    texto = re.sub(r'\*(.+?)\*', r'\1', texto)
    texto = re.sub(r'__(.+?)__', r'\1', texto)
    texto = re.sub(r'_(.+?)_', r'\1', texto)
    texto = re.sub(r'~~(.+?)~~', r'\1', texto)
    texto = re.sub(r'`(.+?)`', r'\1', texto)
    
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    texto = emoji_pattern.sub(r'', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    return texto


def hablar_interruptible(texto):
    """Función de síntesis de voz que puede ser interrumpida"""
    global voz_activa, detener_voz_flag
    
    if detener_voz_flag:
        return
    
    voz_activa = True
    temp_file = "temp_audio.mp3"
    
    try:
        tts = gTTS(text=texto, lang="es")
        tts.save(temp_file)
        
        sistema = platform.system()
        
        if sistema == "Windows":
            os.system(f'start {temp_file}')
        elif sistema == "Darwin":
            os.system(f'afplay {temp_file}')
        else:
            os.system(f'mpg123 {temp_file} > /dev/null 2>&1')
        
        # Esperar con posibilidad de interrupción
        duracion = len(texto) * 0.05
        inicio = time.time()
        while time.time() - inicio < duracion:
            if detener_voz_flag:
                if sistema == "Linux":
                    os.system("killall mpg123 > /dev/null 2>&1")
                break
            time.sleep(0.1)
        
    except Exception as e:
        logger.error(f"Error en hablar_interruptible: {e}")
    finally:
        voz_activa = False
        try:
            if os.path.exists(temp_file):
                time.sleep(0.5)
                os.remove(temp_file)
        except:
            pass


# ============== WORKER PARA CHAT ==============
class ChatWorker(QThread):
    """Worker para generar respuestas en el chat sin bloquear la UI"""
    response_ready = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, pregunta):
        super().__init__()
        self.pregunta = pregunta
    
    def run(self):
        try:
            respuesta = generar_respuesta(self.pregunta)
            self.response_ready.emit(respuesta)
        except Exception as e:
            logger.error(f"Error al generar respuesta: {e}")
            self.error_occurred.emit("Lo siento, ocurrió un error al procesar tu mensaje.")


# ============== WORKER PARA VOZ ==============
class VoiceWorker(QThread):
    """Thread para modo voz continuo con interrupción"""
    message_received = Signal(str)
    response_ready = Signal(str)
    status_updated = Signal(str)
    should_stop = Signal()
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.pausar_escucha = False
    
    def run(self):
        global voz_activa, detener_voz_flag
        
        while self.running:
            if voz_activa or self.pausar_escucha:
                time.sleep(0.1)
                continue
            
            self.status_updated.emit("🎤 Escuchando...")
            comando = escuchar()
            
            if comando == "ERROR_MIC":
                self.status_updated.emit("❌ Error de micrófono")
                break
            
            if not comando:
                continue
            
            # Interrumpir si está hablando
            if voz_activa:
                detener_voz_flag = True
                time.sleep(0.3)
                detener_voz_flag = False
            
            self.message_received.emit(f"Tú: {comando}")
            
            if any(palabra in comando for palabra in ["adiós", "adios", "eso es todo", "termina"]):
                respuesta = "Hasta luego. Fue un placer ayudarte."
                self.response_ready.emit(respuesta)
                hablar_interruptible(limpiar_texto_para_voz(respuesta))
                self.should_stop.emit()
                break
            
            self.status_updated.emit("🧠 Procesando...")
            respuesta, _ = procesar_comando(comando)
            
            if respuesta:
                self.response_ready.emit(respuesta)
                self.status_updated.emit("💬 Respondiendo...")
                hablar_interruptible(limpiar_texto_para_voz(respuesta))
        
        self.status_updated.emit("💤 Modo voz desactivado")
    
    def stop(self):
        global detener_voz_flag
        detener_voz_flag = True
        self.running = False
        time.sleep(0.3)


# ============== WORKER PARA ESCUCHAR (FLOTANTE) ==============
class ListenWorker(QThread):
    """Thread para escuchar sin bloquear la UI"""
    command_received = Signal(str)
    status_changed = Signal(str)
    listening_started = Signal()
    listening_stopped = Signal()
    
    def __init__(self):
        super().__init__()
        self.should_stop = False
    
    def run(self):
        self.listening_started.emit()
        self.status_changed.emit("🎤 Escuchando...")
        
        # Detener cualquier TTS activo antes de escuchar
        if tts_is_playing():
            stop_tts()
            time.sleep(0.1)
        
        comando = escuchar()
        
        self.listening_stopped.emit()
        
        if comando == "ERROR_MIC":
            self.status_changed.emit("❌ Error de micrófono")
            self.command_received.emit("")
            return
        
        if comando:
            self.status_changed.emit("🧠 Procesando...")
            self.command_received.emit(comando)
        else:
            self.status_changed.emit("⚠️ No te escuché")
            self.command_received.emit("")
    
    def stop_listening(self):
        self.should_stop = True


# ============== WORKER PARA PROCESAR RESPUESTA (FLOTANTE) ==============
class ProcessWorker(QThread):
    """Thread para procesar comando y responder"""
    response_ready = Signal(str)
    status_changed = Signal(str)
    
    def __init__(self, comando):
        super().__init__()
        self.comando = comando
    
    def run(self):
        try:
            from src.main import hablar
            respuesta, _ = procesar_comando(self.comando)
            
            if respuesta:
                self.status_changed.emit("💬 Respondiendo...")
                self.response_ready.emit(respuesta)
                
                # Hablar la respuesta
                hablar(respuesta)
                
                # Esperar a que termine de hablar
                while tts_is_playing():
                    time.sleep(0.1)
                
                self.status_changed.emit("✅ Listo")
            else:
                self.status_changed.emit("⚠️ Sin respuesta")
        except Exception as e:
            self.status_changed.emit(f"❌ Error: {str(e)}")


# ============== INDICADOR "ESCRIBIENDO..." ==============
class TypingIndicator(QWidget):
    """Indicador animado de "Aurora está escribiendo..." """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.phase = 0.0
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        
        self.label = QLabel("Aurora está escribiendo")
        self.label.setFont(QFont("Segoe UI", 11))
        self.label.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent;")
        
        self.dot1 = QLabel("●")
        self.dot2 = QLabel("●")
        self.dot3 = QLabel("●")
        
        for dot in [self.dot1, self.dot2, self.dot3]:
            dot.setFont(QFont("Segoe UI", 14))
            dot.setFixedWidth(15)
        
        layout.addWidget(self.label)
        layout.addWidget(self.dot1)
        layout.addWidget(self.dot2)
        layout.addWidget(self.dot3)
        layout.addStretch()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(150)
    
    def update_animation(self):
        self.phase = (self.phase + 1) % 3
        
        import math
        hue_offset = (self.phase * 120) % 360
        
        for i, dot in enumerate([self.dot1, self.dot2, self.dot3]):
            if i == self.phase:
                dot.setStyleSheet(f"color: {COLORS['cyan']}; background: transparent;")
            elif i == (self.phase - 1) % 3:
                dot.setStyleSheet(f"color: {COLORS['magenta']}; background: transparent;")
            else:
                dot.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent;")


# ============== FONDO ANIMADO ==============
class AnimatedBackground(QWidget):
    """Fondo animado con gradiente líquido"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.color_phase = 0.0
        
        self.color_timer = QTimer(self)
        self.color_timer.timeout.connect(self.update_animation)
        self.color_timer.start(50)
    
    def update_animation(self):
        self.color_phase = (self.color_phase + 0.005) % 1.0
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        import math
        phase = self.color_phase * 2 * math.pi
        
        center_x = self.width() / 2 + math.cos(phase) * self.width() * 0.3
        center_y = self.height() / 2 + math.sin(phase * 0.7) * self.height() * 0.3
        
        gradient = QRadialGradient(center_x, center_y, max(self.width(), self.height()))
        
        # Transición: Azul oscuro → Magenta oscuro → Cian oscuro
        if self.color_phase < 0.33:
            t = self.color_phase / 0.33
            gradient.setColorAt(0.0, QColor(10, 14, 39))
            gradient.setColorAt(0.3, QColor(
                int(26 + (191 - 26) * t),
                int(35 + (0 - 35) * t),
                int(122 + (255 - 122) * t)
            ))
            gradient.setColorAt(1.0, QColor(10, 14, 39))
        elif self.color_phase < 0.66:
            t = (self.color_phase - 0.33) / 0.33
            gradient.setColorAt(0.0, QColor(10, 14, 39))
            gradient.setColorAt(0.3, QColor(
                int(191 + (0 - 191) * t),
                int(0 + (217 - 0) * t),
                int(255)
            ))
            gradient.setColorAt(1.0, QColor(10, 14, 39))
        else:
            t = (self.color_phase - 0.66) / 0.34
            gradient.setColorAt(0.0, QColor(10, 14, 39))
            gradient.setColorAt(0.3, QColor(
                int(0 + (26 - 0) * t),
                int(217 + (35 - 217) * t),
                int(255 + (122 - 255) * t)
            ))
            gradient.setColorAt(1.0, QColor(10, 14, 39))
        
        painter.fillRect(self.rect(), gradient)


        """
Interfaz gráfica mejorada de Aurora
PARTE 2/3: Botones, Widgets y FloatingVoiceWidget
"""

# ============== BOTÓN LÍQUIDO ==============
class LiquidButton(QPushButton):
    """Botón circular con animación líquida de colores"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)
        self.color_phase = 0.0
        self.scale = 1.0
        
        self.color_timer = QTimer(self)
        self.color_timer.timeout.connect(self.update_colors)
        self.color_timer.start(30)
        
        self.scale_animation = QPropertyAnimation(self, b"scale_value")
        self.scale_animation.setDuration(3000)
        self.scale_animation.setStartValue(0.92)
        self.scale_animation.setEndValue(1.08)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.scale_animation.setLoopCount(-1)
        
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    
    def start_animation(self):
        self.scale_animation.start()
    
    def stop_animation(self):
        self.scale_animation.stop()
        self.scale = 1.0
        self.update()
    
    def update_colors(self):
        self.color_phase = (self.color_phase + 0.01) % 1.0
        self.update()
    
    def get_scale_value(self):
        return self.scale
    
    def set_scale_value(self, value):
        self.scale = value
        self.update()
    
    scale_value = property(get_scale_value, set_scale_value)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        import math
        phase = self.color_phase * 2 * math.pi
        
        r1 = int(191 + (0 - 191) * abs(math.sin(phase)))
        g1 = int(0 + (217 - 0) * abs(math.sin(phase)))
        b1 = int(255)
        
        r2 = int(255 + (191 - 255) * abs(math.cos(phase)))
        g2 = int(0 + (0 - 0) * abs(math.cos(phase)))
        b2 = int(128 + (255 - 128) * abs(math.cos(phase)))
        
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(r1, g1, b1))
        gradient.setColorAt(0.5, QColor(COLORS['magenta']))
        gradient.setColorAt(1.0, QColor(r2, g2, b2))
        
        size = min(self.width(), self.height()) * self.scale
        x = (self.width() - size) / 2
        y = (self.height() - size) / 2
        
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(x), int(y), int(size), int(size))
        
        painter.setPen(QColor('white'))
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())

    @Property(float)
    def scale_value(self):
        return self.scale

    @scale_value.setter
    def scale_value(self, value):
        self.scale = value
        self.update()

# ============== WIDGET FLOTANTE CON VOZ ==============
def __init__(self, parent=None):
    super().__init__(
        parent,
        Qt.WindowType.Tool | 
        Qt.WindowType.FramelessWindowHint | 
        Qt.WindowType.WindowStaysOnTopHint
    )
    
    # Estado
    self.is_listening = False
    self.is_processing = False
    self.color_phase = 0.0
    self.pulse_scale = 1.0
    self.dragging = False
    self.offset = QPoint()
    
    # Workers
    self.listen_worker = None
    self.process_worker = None
    
    # Configuración
    self.setFixedSize(80, 80)
    
    # ⭐ NUEVO: Hacer el fondo transparente (elimina el cuadrado blanco)
    self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    
    self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    
    # Tooltip
    self.setToolTip("Click para hablar con Aurora\nDoble click para abrir ventana")
    
    # Timer para animación de colores
    self.color_timer = QTimer(self)
    self.color_timer.timeout.connect(self.update_colors)
    self.color_timer.start(30)
    
    # Animación de pulso (solo cuando escucha)
    self.pulse_animation = QPropertyAnimation(self, b"pulse_value")
    self.pulse_animation.setDuration(800)
    self.pulse_animation.setStartValue(0.9)
    self.pulse_animation.setEndValue(1.15)
    self.pulse_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
    self.pulse_animation.setLoopCount(-1)
    
    # Posicionar en esquina inferior derecha
    self.position_at_corner()
    
    # Label de estado
    self.status_label = None
    self.create_status_label()

    
    def position_at_corner(self):
        """Posiciona el widget en la esquina inferior derecha"""
        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 80
        self.move(x, y)
    
    def create_status_label(self):
        """Crea un label flotante para mostrar el estado"""
        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: rgba(10, 14, 39, 220);
                color: white;
                padding: 8px 15px;
                border-radius: 15px;
                border: 1px solid rgba(0, 217, 255, 0.5);
                font-size: 11px;
                font-weight: 600;
            }
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.hide()
    
    def show_status(self, text, duration=3000):
        """Muestra un mensaje de estado temporal"""
        if not self.status_label:
            return
        
        self.status_label.setText(text)
        self.status_label.adjustSize()
        
        # Posicionar arriba del widget
        x = (self.width() - self.status_label.width()) // 2
        y = -self.status_label.height() - 10
        self.status_label.move(x, y)
        self.status_label.show()
        
        # Ocultar después de un tiempo
        if duration > 0:
            QTimer.singleShot(duration, self.status_label.hide)
    
    def update_colors(self):
        """Actualiza la fase de color para animación"""
        if self.is_listening:
            self.color_phase = (self.color_phase + 0.03) % 1.0
        else:
            self.color_phase = (self.color_phase + 0.015) % 1.0
        self.update()
    
    def get_pulse_value(self):
        return self.pulse_scale
    
    def set_pulse_value(self, value):
        self.pulse_scale = value
        self.update()
    
    pulse_value = property(get_pulse_value, set_pulse_value)
    
    def paintEvent(self, event):
        """Dibuja el widget con animación"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        import math
        phase = self.color_phase * 2 * math.pi
        
        # Colores según estado
        if self.is_listening:
            r = int(0 + (191 - 0) * abs(math.sin(phase * 2)))
            g = int(217 + (0 - 217) * abs(math.sin(phase * 2)))
            b = 255
        elif self.is_processing:
            r, g, b = 191, 0, 255
        else:
            if self.color_phase < 0.33:
                t = self.color_phase / 0.33
                r = int(255 + (0 - 255) * t)
                g = int(0 + (217 - 0) * t)
                b = int(128 + (255 - 128) * t)
            elif self.color_phase < 0.66:
                t = (self.color_phase - 0.33) / 0.33
                r = int(0 + (191 - 0) * t)
                g = int(217 + (0 - 217) * t)
                b = 255
            else:
                t = (self.color_phase - 0.66) / 0.34
                r = int(191 + (255 - 191) * t)
                g = int(0)
                b = int(255 + (128 - 255) * t)
        
        # Aplicar escala de pulso
        scale = self.pulse_scale if self.is_listening else 1.0
        size = min(self.width(), self.height()) * scale * 0.85
        x = (self.width() - size) / 2
        y = (self.height() - size) / 2
        
        # Gradiente radial
        gradient = QRadialGradient(self.width() / 2, self.height() / 2, size / 2)
        gradient.setColorAt(0.0, QColor(r, g, b))
        gradient.setColorAt(0.5, QColor(int(r * 0.8), int(g * 0.8), int(b * 0.8)))
        gradient.setColorAt(1.0, QColor(int(r * 0.6), int(g * 0.6), int(b * 0.6)))
        
        # Dibujar círculo
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(x), int(y), int(size), int(size))
        
        # Dibujar letra "A" o ícono
        painter.setPen(QColor('white'))
        if self.is_listening:
            painter.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "🎤")
        elif self.is_processing:
            painter.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "⚙️")
        else:
            painter.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "A")
        
        # Anillo exterior cuando escucha
        if self.is_listening:
            ring_size = size * 1.2
            ring_x = (self.width() - ring_size) / 2
            ring_y = (self.height() - ring_size) / 2
            
            painter.setPen(QColor(0, 217, 255, 100))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(int(ring_x), int(ring_y), int(ring_size), int(ring_size))
    
    def mousePressEvent(self, event):
        """Maneja click y arrastre"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.pos()
            self.click_pos = event.globalPosition().toPoint()
    
    def mouseMoveEvent(self, event):
        """Permite arrastrar el widget"""
        if self.dragging:
            self.move(self.mapToGlobal(event.pos() - self.offset))
    
    def mouseReleaseEvent(self, event):
        """Detecta click vs arrastre"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            
            if (event.globalPosition().toPoint() - self.click_pos).manhattanLength() < 10:
                self.on_click()
    
    def mouseDoubleClickEvent(self, event):
        """Doble click restaura la ventana principal"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.restore_window.emit()
    
    def on_click(self):
        """Maneja el click simple - activa escucha por voz"""
        if self.is_listening or self.is_processing:
            return
        
        self.start_listening()
    
    def start_listening(self):
        """Inicia la escucha por voz"""
        if self.listen_worker and self.listen_worker.isRunning():
            return
        
        self.is_listening = True
        self.pulse_animation.start()
        self.show_status("🎤 Escuchando...", 0)
        
        self.listen_worker = ListenWorker()
        self.listen_worker.command_received.connect(self.on_command_received)
        self.listen_worker.status_changed.connect(self.show_status)
        self.listen_worker.listening_stopped.connect(self.stop_listening_animation)
        self.listen_worker.start()
    
    def stop_listening_animation(self):
        """Detiene la animación de escucha"""
        self.is_listening = False
        self.pulse_animation.stop()
        self.pulse_scale = 1.0
        self.update()
    
    def on_command_received(self, comando):
        """Procesa el comando recibido"""
        if not comando:
            self.show_status("⚠️ No te escuché", 2000)
            return
        
        self.show_status(f"💭 {comando[:30]}...", 2000)
        
        self.is_processing = True
        
        self.process_worker = ProcessWorker(comando)
        self.process_worker.response_ready.connect(self.on_response_ready)
        self.process_worker.status_changed.connect(self.show_status)
        self.process_worker.finished.connect(self.on_processing_finished)
        self.process_worker.start()
    
    def on_response_ready(self, respuesta):
        """Cuando la respuesta está lista"""
        pass
    
    def on_processing_finished(self):
        """Cuando termina el procesamiento"""
        self.is_processing = False
        self.update()
        QTimer.singleShot(2000, lambda: self.show_status("", 0))
    
    def cleanup(self):
        """Limpia los workers antes de cerrar"""
        if self.listen_worker:
            self.listen_worker.should_stop = True
            self.listen_worker.wait()
        
        if self.process_worker:
            self.process_worker.wait()


# ============== BURBUJA DE CHAT ==============
class ChatBubble(QFrame):
    """Burbuja de mensaje estilo chat futurista con tamaño adaptable"""
    edit_requested = Signal(str)
    copy_requested = Signal(str)
    
    def __init__(self, text, is_user=True, parent=None):
        super().__init__(parent)
        self.text_content = text
        self.is_user = is_user
        
        bg_color = COLORS['magenta'] if is_user else COLORS['surface_light']
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 16px;
                padding: 0px;
                border: 1px solid {'rgba(191, 0, 255, 0.3)' if is_user else 'rgba(0, 217, 255, 0.2)'};
            }}
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 10)
        main_layout.setSpacing(8)
        
        # Texto del mensaje
        label = QLabel(text)
        label.setWordWrap(True)
        label.setFont(QFont("Segoe UI", 11))
        label.setStyleSheet(f"color: {COLORS['text']}; background-color: transparent;")
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        main_layout.addWidget(label)
        
        # Botones de acciones (solo para mensajes del usuario)
        if is_user:
            actions_layout = QHBoxLayout()
            actions_layout.setSpacing(8)
            actions_layout.setContentsMargins(0, 4, 0, 0)
            
            btn_edit = QPushButton("✏️ Editar")
            btn_copy = QPushButton("📋 Copiar")
            
            for btn in [btn_edit, btn_copy]:
                btn.setFixedHeight(28)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(255, 255, 255, 0.1);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        border-radius: 6px;
                        color: {COLORS['text']};
                        font-size: 10px;
                        padding: 4px 12px;
                    }}
                    QPushButton:hover {{
                        background: rgba(255, 255, 255, 0.2);
                    }}
                """)
            
            btn_edit.clicked.connect(lambda: self.edit_requested.emit(self.text_content))
            btn_copy.clicked.connect(lambda: self.copy_requested.emit(self.text_content))
            
            actions_layout.addWidget(btn_edit)
            actions_layout.addWidget(btn_copy)
            actions_layout.addStretch()
            
            main_layout.addLayout(actions_layout)
        
        self.adjustSize()

        """
Interfaz gráfica mejorada de Aurora
PARTE 3/3 FINAL: Ventana Principal AuroraWindow
"""

# ============== VENTANA PRINCIPAL ==============
class AuroraWindow(QWidget):
    """Ventana principal con selector de modo"""
    
    def __init__(self):
        super().__init__()
        self.voice_worker = None
        self.chat_worker = None
        self.chat_input = None
        self.liquid_button = None
        self.floating_voice_widget = None  # NUEVO: Widget flotante con voz
        self.animated_bg = None
        self.typing_indicator = None
        self.mic_recording = False
        self.configurar_ventana()
        self.crear_interfaz()
        self.mostrar_selector_modo()
    
    def configurar_ventana(self):
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(100, 100, 1000, 750)
        self.setStyleSheet(f"background-color: {COLORS['background']};")
    
    def crear_interfaz(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
    
    def limpiar_layout(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()
    
    def changeEvent(self, event):
        """Detectar cambios de estado de la ventana"""
        if event.type() == event.Type.WindowStateChange:
            # Si se minimiza, mostrar flotante
            if self.isMinimized():
                self.show_floating_only()
            # Si se restaura o maximiza, ocultar flotante
            elif self.isMaximized() or self.windowState() == Qt.WindowState.WindowNoState:
                self.hide_floating()
        super().changeEvent(event)
    
    def show_floating_only(self):
        """Muestra el widget flotante SIN ocultar la ventana principal"""
        if not self.floating_voice_widget:
            self.floating_voice_widget = FloatingVoiceWidget()
            self.floating_voice_widget.restore_window.connect(self.restore_from_floating)
        
        self.floating_voice_widget.show()
        # La ventana NO se oculta
    
    def hide_floating(self):
        """Oculta el widget flotante cuando la ventana está activa"""
        if self.floating_voice_widget:
            self.floating_voice_widget.hide()
    
    def restore_from_floating(self):
        """Restaura la ventana desde el widget flotante"""
        # Restaurar ventana
        self.showNormal()
        self.activateWindow()
        
        # Ocultar widget flotante (no destruirlo)
        if self.floating_voice_widget:
            self.floating_voice_widget.hide()
    
    def showEvent(self, event):
        """Detecta cuando la ventana se muestra"""
        super().showEvent(event)
        # Si la ventana se muestra y NO está minimizada, ocultar flotante
        if not self.isMinimized():
            self.hide_floating()
    
    def closeEvent(self, event):
        """Limpia recursos al cerrar la aplicación"""
        if self.floating_voice_widget:
            self.floating_voice_widget.cleanup()
            self.floating_voice_widget.close()
        
        if self.voice_worker:
            self.voice_worker.stop()
            self.voice_worker.wait()
        
        event.accept()
    
  
    
    def mostrar_selector_modo(self):
        self.limpiar_layout()
        
        # Fondo animado
        self.animated_bg = AnimatedBackground(self)
        self.animated_bg.setGeometry(self.rect())
        self.animated_bg.lower()
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(50)
        
        titulo = QLabel("")
        titulo.setPixmap(QPixmap("assets/AUR.png").scaled(500, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        
        subtitulo = QLabel("Asistente Inteligente")
        subtitulo.setFont(QFont("Segoe UI", 18))
        subtitulo.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent; letter-spacing: 3px;")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(30)
        
        btn_chat = QPushButton("CHAT")
        btn_voz = QPushButton("VOZ")
        
        for btn in [btn_chat, btn_voz]:
            btn.setFixedSize(200, 70)
            btn.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['cyan']}, stop:1 {COLORS['magenta']});
                    color: white;
                    border: none;
                    border-radius: 35px;
                    font-weight: 700;
                    letter-spacing: 3px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['magenta']}, stop:1 {COLORS['pink']});
                }}
                QPushButton:pressed {{ background: {COLORS['surface_light']}; }}
            """)
        
        btn_chat.clicked.connect(self.mostrar_modo_chat)
        btn_voz.clicked.connect(self.mostrar_modo_voz)
        
        botones_layout.addWidget(btn_chat)
        botones_layout.addWidget(btn_voz)
        
        layout.addStretch()
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        layout.addSpacing(60)
        layout.addLayout(botones_layout)
        layout.addStretch()
        
        self.main_layout.addWidget(container)
        pass
    
    def resizeEvent(self, event):
        """Actualizar tamaño del fondo animado"""
        super().resizeEvent(event)
        if self.animated_bg:
            self.animated_bg.setGeometry(self.rect())
            pass
    
    # ============== MODO CHAT ==============
    def mostrar_modo_chat(self):
        self.limpiar_layout()
        
        container = QWidget()
        container.setStyleSheet(f"background-color: {COLORS['background']};")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        header.setSpacing(15)
        
        titulo = QLabel("Chat con Aurora")
        titulo.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {COLORS['cyan']}; background: transparent;")
        
        # NUEVO: Botón minimizar a flotante
        btn_minimizar = QPushButton("💬 FLOTANTE")
        btn_minimizar.setFixedSize(140, 40)
        btn_minimizar.clicked.connect(self.show_floating_only)
        btn_minimizar.setStyleSheet(f"""
            QPushButton {{
                color: {COLORS['text']};
                background: {COLORS['surface']};
                border: 1px solid {COLORS['magenta']};
                padding: 8px 20px;
                border-radius: 20px;
                font-weight: 600;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: {COLORS['surface_light']};
                border: 1px solid {COLORS['pink']};
            }}
        """)
        
        btn_volver = QPushButton("VOLVER")
        btn_volver.setFixedSize(120, 40)
        btn_volver.clicked.connect(self.volver_a_inicio)
        btn_volver.setStyleSheet(f"""
            QPushButton {{
                color: {COLORS['text']};
                background: {COLORS['surface']};
                border: 1px solid {COLORS['cyan']};
                padding: 8px 20px;
                border-radius: 20px;
                font-weight: 600;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: {COLORS['surface_light']};
                border: 1px solid {COLORS['magenta']};
            }}
        """)
        
        header.addWidget(titulo)
        header.addStretch()
        header.addWidget(btn_minimizar)
        header.addWidget(btn_volver)
        
        # Área de chat con scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{ background: {COLORS['surface']}; width: 8px; border-radius: 4px; }}
            QScrollBar::handle:vertical {{ background: {COLORS['cyan']}; border-radius: 4px; }}
        """)
        
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setSpacing(15)
        self.chat_layout.addStretch()
        scroll.setWidget(self.chat_container)
        
        # Input container
        input_container = QFrame()
        input_container.setStyleSheet(f"""
            QFrame {{ background: {COLORS['surface']}; border-radius: 25px; border: 1px solid {COLORS['surface_light']}; }}
        """)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(15, 10, 15, 10)
        input_layout.setSpacing(10)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Escribe tu mensaje...")
        self.chat_input.setFont(QFont("Segoe UI", 12))
        self.chat_input.setStyleSheet(f"""
            QLineEdit {{ background: transparent; border: none; color: {COLORS['text']}; padding: 8px; }}
            QLineEdit::placeholder {{ color: {COLORS['text_dim']}; }}
        """)
        self.chat_input.returnPressed.connect(self.enviar_mensaje_chat)
        
        # Botón de micrófono (toggle)
        self.btn_mic = QPushButton("🎤")
        self.btn_mic.setFixedSize(45, 45)
        self.btn_mic.setCheckable(True)
        self.btn_mic.clicked.connect(self.toggle_mic_chat)
        self.btn_mic.setStyleSheet(f"""
            QPushButton {{ background: {COLORS['surface_light']}; border: none; border-radius: 22px; color: white; font-size: 16px; }}
            QPushButton:hover {{ background: {COLORS['magenta']}; }}
            QPushButton:checked {{ background: {COLORS['cyan']}; }}
        """)
        
        # Botón enviar/pausar
        self.btn_send = QPushButton("ENVIAR")
        self.btn_send.setFixedHeight(45)
        self.btn_send.clicked.connect(self.enviar_o_pausar)
        self.btn_send.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['cyan']}, stop:1 {COLORS['magenta']});
                border: none;
                border-radius: 22px;
                padding: 0 25px;
                color: white;
                font-weight: bold;
                font-size: 12px;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['magenta']}, stop:1 {COLORS['pink']});
            }}
        """)
        
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(self.btn_mic)
        input_layout.addWidget(self.btn_send)
        
        main_layout.addLayout(header)
        main_layout.addWidget(scroll, 1)
        main_layout.addWidget(input_container)
        
        self.main_layout.addWidget(container)
        
        # Mensaje de bienvenida
        self.agregar_mensaje_chat("¡Hola! Soy Aurora. ¿En qué puedo ayudarte hoy?", is_user=False)
    
    def volver_a_inicio(self):
        """Volver al selector de modo"""
        self.chat_input = None
        self.chat_worker = None
        self.typing_indicator = None
        self.mostrar_selector_modo()
    
    def agregar_mensaje_chat(self, texto, is_user=True):
        """Agrega una burbuja de chat"""
        bubble = ChatBubble(texto, is_user)
        
        # Conectar señales de editar y copiar
        if is_user:
            bubble.edit_requested.connect(self.editar_mensaje)
            bubble.copy_requested.connect(self.copiar_mensaje)
        
        # Ancho adaptable (máximo 70% del ancho disponible)
        max_width = int(self.width() * 0.7)
        bubble.setMaximumWidth(max_width)
        
        container = QHBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
        if is_user:
            container.addStretch()
            container.addWidget(bubble)
        else:
            container.addWidget(bubble)
            container.addStretch()
        
        # Insertar antes del stretch final
        self.chat_layout.insertLayout(self.chat_layout.count() - 1, container)
        
        # Scroll automático
        QTimer.singleShot(50, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        """Hacer scroll hasta el final del chat"""
        scroll_area = self.chat_container.parent()
        if isinstance(scroll_area, QScrollArea):
            scroll_bar = scroll_area.verticalScrollBar()
            scroll_bar.setValue(scroll_bar.maximum())
    
    def mostrar_typing_indicator(self):
        """Muestra el indicador de 'escribiendo...'"""
        if not self.typing_indicator:
            self.typing_indicator = TypingIndicator()
            container = QHBoxLayout()
            container.addWidget(self.typing_indicator)
            container.addStretch()
            self.chat_layout.insertLayout(self.chat_layout.count() - 1, container)
            self.scroll_to_bottom()
    
    def ocultar_typing_indicator(self):
        """Oculta el indicador de 'escribiendo...'"""
        if self.typing_indicator:
            self.typing_indicator.setParent(None)
            self.typing_indicator.deleteLater()
            self.typing_indicator = None
    
    def enviar_mensaje_chat(self):
        """Envía mensaje de texto"""
        if not self.chat_input or self.chat_worker:
            return
        
        texto = self.chat_input.text().strip()
        if not texto:
            return
        
        # Agregar mensaje del usuario
        self.agregar_mensaje_chat(texto, is_user=True)
        self.chat_input.clear()
        
        # Cambiar botón a PAUSAR
        self.btn_send.setText("⏸ PAUSAR")
        
        # Mostrar indicador
        self.mostrar_typing_indicator()
        
        # Crear worker para generar respuesta
        self.chat_worker = ChatWorker(texto)
        self.chat_worker.response_ready.connect(self.on_response_ready)
        self.chat_worker.error_occurred.connect(self.on_response_error)
        self.chat_worker.start()
    
    def on_response_ready(self, respuesta):
        """Callback cuando la respuesta está lista"""
        self.ocultar_typing_indicator()
        self.agregar_mensaje_chat(respuesta, is_user=False)
        self.btn_send.setText("ENVIAR")
        self.chat_worker = None
    
    def on_response_error(self, error):
        """Callback cuando hay un error"""
        self.ocultar_typing_indicator()
        self.agregar_mensaje_chat(error, is_user=False)
        self.btn_send.setText("ENVIAR")
        self.chat_worker = None
    
    def enviar_o_pausar(self):
        """Enviar mensaje o pausar generación"""
        if self.chat_worker and self.chat_worker.isRunning():
            # Pausar generación
            self.chat_worker.terminate()
            self.chat_worker = None
            self.ocultar_typing_indicator()
            self.btn_send.setText("ENVIAR")
        else:
            # Enviar mensaje
            self.enviar_mensaje_chat()
    
    def toggle_mic_chat(self):
        """Toggle del micrófono en el chat"""
        if self.btn_mic.isChecked():
            # Activar grabación
            self.btn_mic.setText("⏹")
            self.chat_input.setPlaceholderText("🎤 Escuchando...")
            self.iniciar_grabacion_chat()
        else:
            # Detener grabación
            self.btn_mic.setText("🎤")
            self.chat_input.setPlaceholderText("Escribe tu mensaje...")
            self.detener_grabacion_chat()
    
    def iniciar_grabacion_chat(self):
        """Inicia la grabación de voz en el chat"""
        def escuchar_comando():
            comando = escuchar()
            
            def actualizar_ui():
                if not self.chat_input:
                    return
                
                self.btn_mic.setChecked(False)
                self.btn_mic.setText("🎤")
                
                if comando and comando != "ERROR_MIC":
                    self.chat_input.setText(comando)
                
                self.chat_input.setPlaceholderText("Escribe tu mensaje...")
            
            QTimer.singleShot(0, actualizar_ui)
        
        threading.Thread(target=escuchar_comando, daemon=True).start()
    
    def detener_grabacion_chat(self):
        """Detiene la grabación (ya manejado por el toggle)"""
        pass
    
    def editar_mensaje(self, texto):
        """Edita un mensaje (lo carga en el input)"""
        if self.chat_input:
            self.chat_input.setText(texto)
            self.chat_input.setFocus()
    
    def copiar_mensaje(self, texto):
        """Copia un mensaje al portapapeles"""
        clipboard = QApplication.clipboard()
        clipboard.setText(texto)
    
    # ============== MODO VOZ ==============
    def mostrar_modo_voz(self):
        self.limpiar_layout()
        
        threading.Thread(
            target=lambda: hablar_interruptible(limpiar_texto_para_voz("Modo voz activado. Presiona el botón para hablar.")),
            daemon=True
        ).start()
        
        container = QWidget()
        container.setStyleSheet(f"background-color: {COLORS['background']};")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(40)
        
        # Header con título más pequeño
        header = QHBoxLayout()
        titulo = QLabel("Modo Voz")
        titulo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color: {COLORS['cyan']}; background: transparent; letter-spacing: 2px;")
        
        # NUEVO: Botón minimizar a flotante
        btn_minimizar = QPushButton("💬 FLOTANTE")
        btn_minimizar.setFixedSize(140, 40)
        btn_minimizar.clicked.connect(self.show_floating_only)
        btn_minimizar.setStyleSheet(f"""
            QPushButton {{
                color: {COLORS['text']};
                background: {COLORS['surface']};
                border: 1px solid {COLORS['magenta']};
                padding: 8px 20px;
                border-radius: 20px;
                font-weight: 600;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: {COLORS['surface_light']};
                border: 1px solid {COLORS['pink']};
            }}
        """)
        
        btn_volver = QPushButton("VOLVER")
        btn_volver.setFixedSize(120, 40)
        btn_volver.clicked.connect(lambda: [self.detener_voz(), self.mostrar_selector_modo()])
        btn_volver.setStyleSheet(f"""
            QPushButton {{
                color: {COLORS['text']};
                background: {COLORS['surface']};
                border: 1px solid {COLORS['cyan']};
                padding: 8px 20px;
                border-radius: 20px;
                font-weight: 600;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: {COLORS['surface_light']};
            }}
        """)
        
        header.addWidget(titulo)
        header.addStretch()
        header.addWidget(btn_minimizar)
        header.addWidget(btn_volver)
        
        # Botón líquido
        self.liquid_button = LiquidButton()
        self.liquid_button.setText("INICIAR")
        self.liquid_button.clicked.connect(self.toggle_voz)
        
        # Estado
        self.voice_status = QLabel("Presiona el botón para comenzar")
        self.voice_status.setFont(QFont("Segoe UI", 15))
        self.voice_status.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent;")
        self.voice_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addLayout(header)
        main_layout.addStretch()
        main_layout.addWidget(self.liquid_button, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addSpacing(30)
        main_layout.addWidget(self.voice_status)
        main_layout.addStretch()
        
        self.main_layout.addWidget(container)
    
    def toggle_voz(self):
        """Toggle del modo voz"""
        if self.voice_worker and self.voice_worker.isRunning():
            self.detener_voz()
        else:
            self.iniciar_voz()
    
    def iniciar_voz(self):
        """Inicia el modo voz continuo"""
        if self.liquid_button:
            self.liquid_button.setText("DETENER")
            self.liquid_button.start_animation()
        
        self.voice_status.setText("🎤 Escuchando continuamente...")
        self.voice_status.setStyleSheet(f"color: {COLORS['cyan']}; background: transparent;")
        
        self.voice_worker = VoiceWorker()
        self.voice_worker.status_updated.connect(lambda msg: self.voice_status.setText(msg))
        self.voice_worker.should_stop.connect(self.detener_voz)
        self.voice_worker.start()
    
    def detener_voz(self):
        """Detiene el modo voz (funciona incluso si está hablando)"""
        global detener_voz_flag
        detener_voz_flag = True
        
        if self.voice_worker:
            self.voice_worker.stop()
            self.voice_worker.wait()
        
        if self.liquid_button:
            self.liquid_button.setText("INICIAR")
            self.liquid_button.stop_animation()
        
        self.voice_status.setText("Presiona el botón para reactivar")
        self.voice_status.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent;")
        
        time.sleep(0.3)
        detener_voz_flag = False


# ============== MAIN ==============
def main():
    """Función principal para ejecutar la interfaz"""
    app = QApplication(sys.argv)
    
    ventana = AuroraWindow()
    ventana.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    main()