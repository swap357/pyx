import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QPushButton, QLabel, QFileDialog
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtSvg import QSvgGenerator

class FluidFlowWidget(QWidget):
    def __init__(self, parent=None):
        super(FluidFlowWidget, self).__init__(parent)
        self.setMinimumSize(600, 400)
        self.particles = []
        self.num_particles = 5000  # Increased default number of particles
        self.flow_scale = 0.005
        self.speed = 1.0
        self.particle_size = 1  # Reduced default particle size for density
        self.time = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for particle in self.particles:
            x, y = particle
            color = self.get_color(x, y)
            painter.setPen(QPen(color, self.particle_size))
            painter.drawPoint(int(x), int(y))

    def get_color(self, x, y):
        # Generate a grayscale color based on the position of the particle
        intensity = int((np.sin(x * 0.01 + y * 0.01) + 1) * 127)
        return QColor(intensity, intensity, intensity)

    def update_simulation(self):
        if not self.particles:
            self.particles = [(np.random.rand() * self.width(), np.random.rand() * self.height()) for _ in range(self.num_particles)]

        new_particles = []
        for x, y in self.particles:
            angle = self.flow_field(x, y)
            dx = np.cos(angle) * self.speed
            dy = np.sin(angle) * self.speed
            new_x = (x + dx) % self.width()
            new_y = (y + dy) % self.height()
            new_particles.append((new_x, new_y))

        self.particles = new_particles
        self.time += 0.01
        self.update()

    def flow_field(self, x, y):
        # Create a flow field using Perlin-like noise
        angle = (np.sin(x * self.flow_scale + self.time) + 
                 np.sin(y * self.flow_scale + self.time) + 
                 np.sin((x + y) * self.flow_scale + self.time)) * np.pi
        return angle

class FluidFlowSimulation(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fluid Flow - Generative Art")
        self.setGeometry(100, 100, 1200, 800)

        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.flow_widget = FluidFlowWidget()
        control_panel = QWidget()
        control_layout = QVBoxLayout()
        control_panel.setLayout(control_layout)

        self.sliders = {}
        slider_params = [
            ('num_particles', 'Number of Particles', 1000, 20000, 5000),  # Increased max particles
            ('flow_scale', 'Flow Scale', 1, 100, 5),
            ('speed', 'Particle Speed', 1, 100, 10),
            ('particle_size', 'Particle Size', 1, 5, 1)  # Reduced max particle size
        ]

        for name, label, min_val, max_val, default in slider_params:
            slider_layout = QHBoxLayout()
            slider_label = QLabel(label)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_val, max_val)
            slider.setValue(default)
            slider.valueChanged.connect(self.update_simulation)
            self.sliders[name] = slider
            slider_layout.addWidget(slider_label)
            slider_layout.addWidget(slider)
            control_layout.addLayout(slider_layout)

        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_sliders)
        export_button = QPushButton("Export SVG")
        export_button.clicked.connect(self.export_svg)

        button_layout = QHBoxLayout()
        button_layout.addWidget(reset_button)
        button_layout.addWidget(export_button)
        control_layout.addLayout(button_layout)

        main_layout.addWidget(self.flow_widget, 3)
        main_layout.addWidget(control_panel, 1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.flow_widget.update_simulation)
        self.timer.start(16)  # Update every 16 ms (approx. 60 FPS)

    def update_simulation(self):
        self.flow_widget.num_particles = self.sliders['num_particles'].value()
        self.flow_widget.flow_scale = self.sliders['flow_scale'].value() / 10000
        self.flow_widget.speed = self.sliders['speed'].value() / 10
        self.flow_widget.particle_size = self.sliders['particle_size'].value()
        self.flow_widget.particles = []  # Reset particles to apply new settings

    def reset_sliders(self):
        default_values = {
            'num_particles': 1000,
            'flow_scale': 5,
            'speed': 10,
            'particle_size': 2
        }
        for name, value in default_values.items():
            self.sliders[name].setValue(value)
        self.flow_widget.time = 0
        self.flow_widget.particles = []

    def export_svg(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save SVG", "", "SVG files (*.svg)")
        if not file_path:
            return  # User cancelled the dialog

        generator = QSvgGenerator()
        generator.setFileName(file_path)
        generator.setSize(QSize(self.flow_widget.width(), self.flow_widget.height()))
        generator.setViewBox(QRectF(0, 0, self.flow_widget.width(), self.flow_widget.height()))
        generator.setTitle("Fluid Flow")
        generator.setDescription("Generated by Fluid Flow gen art")

        painter = QPainter()
        painter.begin(generator)
        
        # Set the background to white
        painter.fillRect(QRectF(0, 0, self.flow_widget.width(), self.flow_widget.height()), QColor(255, 255, 255))

        # Draw particles
        for particle in self.flow_widget.particles:
            x, y = particle
            color = self.flow_widget.get_color(x, y)
            painter.setPen(QPen(color, self.flow_widget.particle_size))
            painter.drawPoint(int(x), int(y))

        painter.end()
        print(f"SVG exported as '{file_path}'")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = FluidFlowSimulation()
    main_window.show()
    sys.exit(app.exec_())