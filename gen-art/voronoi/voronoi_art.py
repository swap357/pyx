import sys
import numpy as np
from scipy.spatial import Voronoi
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QPushButton, QLabel, QFileDialog
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QSize
from PyQt5.QtGui import QPainter, QColor, QPen, QPolygonF
from PyQt5.QtSvg import QSvgGenerator

class VoronoiWidget(QWidget):
    def __init__(self, parent=None):
        super(VoronoiWidget, self).__init__(parent)
        self.setMinimumSize(600, 400)
        self.points = np.array([])  # Initialize as an empty NumPy array
        self.vor = None
        self.num_points = 100  # Increased default number of points
        self.movement_speed = 1.0
        self.time = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.vor is not None:
            for simplex in self.vor.ridge_vertices:
                if -1 not in simplex:
                    p1 = QPointF(*self.vor.vertices[simplex[0]])
                    p2 = QPointF(*self.vor.vertices[simplex[1]])
                    color = self.get_color(p1.x(), p1.y())
                    painter.setPen(QPen(color, 1))  # Reduced line thickness for density
                    painter.drawLine(p1, p2)

    def get_color(self, x, y):
        # Generate a grayscale color based on the position
        intensity = int((np.sin(x * 0.1 + y * 0.1) + 1) * 127)
        return QColor(intensity, intensity, intensity)

    def update_simulation(self):
        if len(self.points) == 0:
            self.points = np.random.rand(self.num_points, 2) * [self.width(), self.height()]

        # Move points in a circular pattern
        theta = np.linspace(0, 2*np.pi, self.num_points) + self.time
        dx = np.cos(theta) * self.movement_speed
        dy = np.sin(theta) * self.movement_speed
        self.points[:, 0] += dx
        self.points[:, 1] += dy

        # Wrap around the edges
        self.points[:, 0] %= self.width()
        self.points[:, 1] %= self.height()

        # Compute Voronoi diagram
        self.vor = Voronoi(self.points)
        self.time += 0.05
        self.update()

class VoronoiArtSimulation(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voronoi Art - Generative Art")
        self.setGeometry(100, 100, 1200, 800)

        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.voronoi_widget = VoronoiWidget()
        control_panel = QWidget()
        control_layout = QVBoxLayout()
        control_panel.setLayout(control_layout)

        self.sliders = {}
        slider_params = [
            ('num_points', 'Number of Points', 10, 500, 100),  # Increased max points
            ('movement_speed', 'Movement Speed', 0, 100, 10),
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

        main_layout.addWidget(self.voronoi_widget, 3)
        main_layout.addWidget(control_panel, 1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.voronoi_widget.update_simulation)
        self.timer.start(50)  # Update every 50 ms

    def update_simulation(self):
        self.voronoi_widget.num_points = self.sliders['num_points'].value()
        self.voronoi_widget.movement_speed = self.sliders['movement_speed'].value() / 10
        self.voronoi_widget.points = []  # Reset points to apply new settings

    def reset_sliders(self):
        default_values = {
            'num_points': 100,
            'movement_speed': 10,
        }
        for name, value in default_values.items():
            self.sliders[name].setValue(value)
        self.voronoi_widget.time = 0
        self.voronoi_widget.points = []

    def export_svg(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save SVG", "", "SVG files (*.svg)")
        if not file_path:
            return  # User cancelled the dialog

        generator = QSvgGenerator()
        generator.setFileName(file_path)
        generator.setSize(QSize(self.voronoi_widget.width(), self.voronoi_widget.height()))
        generator.setViewBox(QRectF(0, 0, self.voronoi_widget.width(), self.voronoi_widget.height()))
        generator.setTitle("Voronoi Art")
        generator.setDescription("Generated by Voronoi Art gen")

        painter = QPainter()
        painter.begin(generator)
        
        # Set the background to white
        painter.fillRect(QRectF(0, 0, self.voronoi_widget.width(), self.voronoi_widget.height()), QColor(255, 255, 255))

        # Draw Voronoi diagram
        if self.voronoi_widget.vor is not None:
            for simplex in self.voronoi_widget.vor.ridge_vertices:
                if -1 not in simplex:
                    p1 = QPointF(*self.voronoi_widget.vor.vertices[simplex[0]])
                    p2 = QPointF(*self.voronoi_widget.vor.vertices[simplex[1]])
                    color = self.voronoi_widget.get_color(p1.x(), p1.y())
                    painter.setPen(QPen(color, 1))  # Reduced line thickness for density
                    painter.drawLine(p1, p2)

        painter.end()
        print(f"SVG exported as '{file_path}'")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = VoronoiArtSimulation()
    main_window.show()
    sys.exit(app.exec_())