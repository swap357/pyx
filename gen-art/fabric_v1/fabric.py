import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QPushButton, QLabel, QFileDialog
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize, QRectF, QPointF
from PyQt5.QtGui import QOpenGLVersionProfile, QSurfaceFormat, QVector3D, QMatrix4x4, QImage, QPainter, QOpenGLFramebufferObject, QColor
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtSvg import QSvgGenerator
from OpenGL.GL import *
from OpenGL.GLU import *
from noise import pnoise2  # Perlin noise function
import io
import os

# Add this import for QPainterPath
from PyQt5.QtGui import QPainterPath

class OpenGLWidget(QGLWidget):
    def __init__(self, parent=None):
        super(OpenGLWidget, self).__init__(parent)
        self.setMinimumSize(600, 400)
        self.lines = []
        self.num_points = 50
        self.num_threads = 1
        self.noise_scale = 0.2
        self.wave_size = 4
        self.movement = 1.0
        self.line_thickness = 0.5
        self.line_spacing = 0.05
        self.frame = 0
        
        # New variables for interaction
        self.last_pos = QPoint()
        self.displacement = QVector3D(0, -5, 0)  # Move the view back a bit
        self.rotation = QVector3D(0, 0, 0)
        self.scale = 0.2  # Reduce initial scale to show more of the art

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        self.update_projection(width, height)

    def update_projection(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = width / height
        # Adjust the orthographic projection to show more of the art
        gluOrtho2D(-10 * aspect, 10 * aspect, -10, 10)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Apply displacement and rotation
        glTranslatef(self.displacement.x(), self.displacement.y(), self.displacement.z())
        glRotatef(self.rotation.x(), 1, 0, 0)
        glRotatef(self.rotation.y(), 0, 1, 0)

        # Apply overall scale
        glScalef(self.scale, self.scale, self.scale)

        glColor4f(0.2, 0.2, 0.2, 0.7)  # Dark grey with alpha
        glLineWidth(self.line_thickness)

        for line in self.lines:
            glBegin(GL_LINE_STRIP)
            for x, y in line:
                glVertex3f(x, y, 0)  # Remove the offset here
            glEnd()

    def update_simulation(self):
        y_base = np.linspace(0, 10, self.num_points)
        distortion_field = self.multi_layer_perlin_noise(self.num_points, self.num_threads, self.noise_scale, 
                                                         octaves=int(self.wave_size), seed=self.frame * 0.01)
        
        self.lines = []
        total_width = (self.num_threads - 1) * self.line_spacing
        start_x = -total_width / 2  # Start from the left of the center

        for i in range(self.num_threads):
            x_base = np.full(self.num_points, start_x + i * self.line_spacing)
            x = x_base + distortion_field[:, i] * self.movement
            y = y_base + distortion_field[:, i] * self.movement * 2
            self.lines.append(list(zip(x, y)))

        self.frame += 1
        self.updateGL()

    def multi_layer_perlin_noise(self, num_points, num_threads, scale, octaves, seed=0):
        noise_field = np.zeros((num_points, num_threads))
        for octave in range(octaves):
            frequency = 2 ** octave
            amplitude = 1 / (frequency ** 0.5)
            for i in range(num_points):
                for j in range(num_threads):
                    x = (i / num_points) * scale * frequency + seed
                    y = (j / num_threads) * scale * frequency + seed
                    noise_field[i][j] += pnoise2(x, y, octaves=1, repeatx=1024, repeaty=1024, base=0) * amplitude
        return noise_field

    def mousePressEvent(self, event):
        self.last_pos = event.pos()

    def mouseMoveEvent(self, event):
        dx = event.x() - self.last_pos.x()
        dy = event.y() - self.last_pos.y()

        if event.buttons() & Qt.LeftButton:
            # Left button drag: translate
            self.displacement += QVector3D(dx / 100, -dy / 100, 0)
        elif event.buttons() & Qt.RightButton:
            # Right button drag: rotate
            self.rotation += QVector3D(dy / 5, dx / 5, 0)

        self.last_pos = event.pos()
        self.updateGL()

    def wheelEvent(self, event):
        # Zoom in/out with mouse wheel
        self.displacement += QVector3D(0, 0, event.angleDelta().y() / 120)
        self.updateGL()

    def render_to_image(self, size):
        fbo = QOpenGLFramebufferObject(size)
        fbo.bind()
        self.resizeGL(size.width(), size.height())
        self.paintGL()
        fbo.release()
        return fbo.toImage()

class OrganicMotionSimulation(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Organic Fabric - https://github.com/swap357/pyx")
        self.setGeometry(100, 100, 1200, 800)

        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.gl_widget = OpenGLWidget()
        control_panel = QWidget()
        control_layout = QVBoxLayout()
        control_panel.setLayout(control_layout)

        self.sliders = {}
        slider_params = [
            ('num_threads', 'Number of Threads', 1, 80, 1),
            ('noise_scale', 'Fabric Texture', 5, 70, None),
            ('wave_size', 'Wave Size', 1, 8, None),
            ('movement', 'Movement Amount', 1, 300, None),
            ('line_thickness', 'Thread Thickness', 1, 20, None),
            ('line_spacing', 'Thread Spacing', 1, 20, None)
        ]

        for name, label, min_val, max_val, default in slider_params:
            slider_layout = QHBoxLayout()
            slider_label = QLabel(label)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_val, max_val)
            if name == 'num_threads':
                slider.setValue(default)
            else:
                slider.setValue(min_val + (max_val - min_val) // 2)
            slider.valueChanged.connect(self.update_simulation)
            self.sliders[name] = slider
            slider_layout.addWidget(slider_label)
            slider_layout.addWidget(slider)
            control_layout.addLayout(slider_layout)

        # Add a slider for overall scale
        self.sliders['scale'] = QSlider(Qt.Horizontal)
        self.sliders['scale'].setRange(1, 100)
        self.sliders['scale'].setValue(70)  # Set to 70% of max value
        self.sliders['scale'].valueChanged.connect(self.update_simulation)
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("Overall Scale"))
        scale_layout.addWidget(self.sliders['scale'])
        control_layout.addLayout(scale_layout)

        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_sliders)
        export_button = QPushButton("Export SVG")
        export_button.clicked.connect(self.export_svg)

        button_layout = QHBoxLayout()
        button_layout.addWidget(reset_button)
        button_layout.addWidget(export_button)
        control_layout.addLayout(button_layout)

        main_layout.addWidget(self.gl_widget, 3)
        main_layout.addWidget(control_panel, 1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.gl_widget.update_simulation)
        self.timer.start(50)  # Update every 50 ms

    def update_simulation(self):
        self.gl_widget.num_threads = self.sliders['num_threads'].value()
        self.gl_widget.noise_scale = self.sliders['noise_scale'].value() / 100
        self.gl_widget.wave_size = self.sliders['wave_size'].value()
        self.gl_widget.movement = self.sliders['movement'].value() / 100
        self.gl_widget.line_thickness = self.sliders['line_thickness'].value() / 10
        self.gl_widget.line_spacing = self.sliders['line_spacing'].value() / 100
        self.gl_widget.scale = self.sliders['scale'].value() / 100
        self.gl_widget.update_simulation()  # Call this to update immediately

    def reset_sliders(self):
        for name, slider in self.sliders.items():
            if name == 'num_threads':
                slider.setValue(1)
            elif name == 'scale':
                slider.setValue(70)  # Set scale to 70% when resetting
            else:
                slider.setValue(slider.minimum() + (slider.maximum() - slider.minimum()) // 2)
        self.gl_widget.frame = 0
        self.gl_widget.displacement = QVector3D(0, -5, 0)  # Reset to initial position
        self.gl_widget.rotation = QVector3D(0, 0, 0)
        self.gl_widget.updateGL()

    def export_svg(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save SVG", "", "SVG files (*.svg)")
        if not file_path:
            return  # User cancelled the dialog

        # A4 size in pixels (assuming 96 DPI)
        width, height = 794, 1123
        margin = 50  # 50 pixel margin

        generator = QSvgGenerator()
        generator.setFileName(file_path)
        generator.setSize(QSize(width, height))
        generator.setViewBox(QRectF(0, 0, width, height))
        generator.setTitle("Organic Fabric")
        generator.setDescription("Generated by Fabric gen @ https://github.com/swap357/pyx")

        painter = QPainter()
        painter.begin(generator)

        # Set the background to white
        painter.fillRect(QRectF(0, 0, width, height), QColor(255, 255, 255))

        # Calculate the bounding box of the art
        min_x = min(min(point[0] for point in line) for line in self.gl_widget.lines)
        max_x = max(max(point[0] for point in line) for line in self.gl_widget.lines)
        min_y = min(min(point[1] for point in line) for line in self.gl_widget.lines)
        max_y = max(max(point[1] for point in line) for line in self.gl_widget.lines)

        # Calculate the scale factor to fit the fabric within the margins
        art_width = max_x - min_x
        art_height = max_y - min_y
        scale_x = (width - 2 * margin) / art_width
        scale_y = (height - 2 * margin) / art_height
        scale = min(scale_x, scale_y)

        # Calculate translation to center the art
        translate_x = (width - art_width * scale) / 2 - min_x * scale
        translate_y = (height - art_height * scale) / 2 - min_y * scale

        # Set up the painter for drawing the lines
        painter.setPen(QColor(64, 64, 64, 180))  # Dark grey with some transparency
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw each line as a path
        for line in self.gl_widget.lines:
            path = QPainterPath()
            first_point = line[0]
            path.moveTo(QPointF(first_point[0] * scale + translate_x, first_point[1] * scale + translate_y))
            for point in line[1:]:
                path.lineTo(QPointF(point[0] * scale + translate_x, point[1] * scale + translate_y))
            painter.drawPath(path)

        painter.end()

        print(f"SVG exported as '{file_path}'")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set OpenGL format
    gl_format = QSurfaceFormat()
    gl_format.setVersion(2, 1)
    gl_format.setProfile(QSurfaceFormat.CoreProfile)
    QSurfaceFormat.setDefaultFormat(gl_format)
    
    main_window = OrganicMotionSimulation()
    main_window.show()
    sys.exit(app.exec_())