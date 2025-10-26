"""
Widget Flotante de Aurora con Activación por Voz
Burbuja persistente que escucha al hacer click
"""
import time
import threading
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, Signal, QThread, Property
from PySide6.QtGui import QPainter, QColor, QRadialGradient, QCursor, QFont
from PySide6.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout

from src.main import escuchar, procesar_comando, hablar, stop_tts, tts_is_playing


# ============== WORKER PARA ESCUCHAR ==============
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


# ============== WORKER PARA PROCESAR RESPUESTA ==============
class ProcessWorker(QThread):
    """Thread para procesar comando y responder"""
    response_ready = Signal(str)
    status_changed = Signal(str)
    
    def __init__(self, comando):
        super().__init__()
        self.comando = comando
    
    def run(self):
        try:
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


# ============== WIDGET FLOTANTE CON VOZ ==============
class FloatingVoiceWidget(QWidget):
    """Widget flotante con animación de escucha y activación por voz"""
    
    restore_window = Signal()  # Señal para restaurar ventana principal
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configurar flags de ventana - CRÍTICO para Debian/X11
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.X11BypassWindowManagerHint  # ← Esencial para Debian
        )

        # Atributos de transparencia
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)
        
        # Estado
        self.is_listening = False
        self.is_processing = False
        self.color_phase = 0.0
        self._pulse_scale = 1.0  # ← Cambiado de self.pulse_scale a self._pulse_scale
        self.dragging = False
        self.offset = QPoint()
        
        # Workers
        self.listen_worker = None
        self.process_worker = None
        
        # Configuración
        self.setFixedSize(80, 80)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Tooltip
        self.setToolTip("Click para hablar con Aurora\nDoble click para abrir ventana")
        
        # Timer para animación de colores
        self.color_timer = QTimer(self)
        self.color_timer.timeout.connect(self.update_colors)
        self.color_timer.start(30)
        
        # Animación de pulso (solo cuando escucha)
        self.pulse_animation = QPropertyAnimation(self, b"pulseScale")  # ← Cambiado a pulseScale
        self.pulse_animation.setDuration(800)
        self.pulse_animation.setStartValue(0.9)
        self.pulse_animation.setEndValue(1.15)
        self.pulse_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.pulse_animation.setLoopCount(-1)
        
        # Posicionar en esquina inferior derecha
        self.position_at_corner()
        
        # Label de estado (opcional, se puede ocultar)
        self.status_label = None
        self.create_status_label()
    
    # ============== PROPIEDAD ANIMABLE ==============
    def getPulseScale(self):
        return self._pulse_scale
    
    def setPulseScale(self, value):
        self._pulse_scale = value
        self.update()
    
    # Propiedad Qt para animación
    pulseScale = Property(float, getPulseScale, setPulseScale)
    
    def position_at_corner(self):
        """Posiciona el widget en la esquina inferior derecha"""
        screen = QApplication.primaryScreen().availableGeometry()  # ← Cambiado a availableGeometry()
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
        scale = self._pulse_scale if self.is_listening else 1.0
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
        
        # Dibujar logo o ícono
        logo = None
        painter.setPen(QColor('white'))
        if self.is_listening:
            painter.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "🎤")
        elif self.is_processing:
            painter.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "⚙️")
        else:
            logo = QPixmap("assets/aurowhite.png")
        
        if logo and not logo.isNull():
            size_img = int(self.width() * 0.5)
            logo = logo.scaled(size_img, size_img, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            x_img = (self.width() - logo.width()) // 2
            y_img = (self.height() - logo.height()) // 2
            painter.drawPixmap(x_img, y_img, logo)

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
            
            # Si se movió poco, es un click
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
        self._pulse_scale = 1.0
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


# ============== FUNCIÓN PARA INTEGRAR EN INTERFAZ.PY ==============
def create_floating_widget(parent_window):
    """
    Crea y retorna el widget flotante.
    
    Uso en interfaz.py:
        self.floating = create_floating_widget(self)
        self.floating.restore_window.connect(self.restore_from_floating)
        self.floating.show()
    """
    widget = FloatingVoiceWidget()
    widget.restore_window.connect(lambda: parent_window.showNormal() or parent_window.activateWindow())
    return widget


# ============== TEST STANDALONE ==============
if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    
    widget = FloatingVoiceWidget()
    widget.show()
    
    print("✅ Widget flotante iniciado")
    print("   • Click: Activar voz")
    print("   • Doble click: Restaurar ventana")
    print("   • Arrastrar: Mover widget")
    
    sys.exit(app.exec())