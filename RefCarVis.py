import numpy as np
from PySide6.QtWidgets import QApplication
import pyqtgraph.opengl as gl
from PySide6.QtGui import QVector3D, QColor
import math

class RefCarVisualizer:
    def __init__(self):
        self.app = QApplication.instance()  # Use existing instance of QApplication
        if self.app is None:
            self.app = QApplication([])

        self.w = CustomGLViewWidget()
        self.w.setBackgroundColor(QColor(0, 0, 0, 0))
        self.w.opts['glOptions'] = {'depthTest': True, 'alpha': True, 'blend': True, 'multisample': True, 'doubleBuffer': True}
        self.w.resize(300, 300)
        self.w.setCameraPosition(pos=QVector3D(0, 0, 0), distance=6, elevation=10, azimuth=5)

        self.tire_FL = gl.GLMeshItem(meshdata=gl.MeshData.sphere(rows=10, cols=10), color=[0, 1, 0, 1.0], smooth=False)
        self.tire_FR = gl.GLMeshItem(meshdata=gl.MeshData.sphere(rows=10, cols=10), color=[0, 1, 0, 1.0], smooth=False)
        self.tire_RL = gl.GLMeshItem(meshdata=gl.MeshData.sphere(rows=10, cols=10), color=[0, 1, 0, 1.0], smooth=False)
        self.tire_RR = gl.GLMeshItem(meshdata=gl.MeshData.sphere(rows=10, cols=10), color=[0, 1, 0, 1.0], smooth=False)
        self.tire_FL.scale(0.45, 0.45, 0.45)
        self.tire_FR.scale(0.45, 0.45, 0.45)
        self.tire_RL.scale(0.45, 0.45, 0.45)
        self.tire_RR.scale(0.45, 0.45, 0.45)
        self.tire_offset = np.array([
            [-1.5, -1.2, 0.45 -1.0],
            [-1.5,  1.2, 0.45 -1.0],
            [ 1.5, -1.2, 0.45 -1.0],
            [ 1.5,  1.2, 0.45 -1.0] 
        ]) 
        self.tire_FL.translate(self.tire_offset[0][0], self.tire_offset[0][1], self.tire_offset[0][2])
        self.tire_FR.translate(self.tire_offset[1][0], self.tire_offset[1][1], self.tire_offset[1][2])
        self.tire_RL.translate(self.tire_offset[2][0], self.tire_offset[2][1], self.tire_offset[2][2])
        self.tire_RR.translate(self.tire_offset[3][0], self.tire_offset[3][1], self.tire_offset[3][2])
        
        self.w.addItem(self.tire_FL)
        self.w.addItem(self.tire_FR)
        self.w.addItem(self.tire_RL)
        self.w.addItem(self.tire_RR)
        
        self.camera_mode = 1
        self.camera_zoom = 5
        self.camera_angle = 15

    def update(self, car_data):
        position = np.array([car_data["position_x"], car_data["position_y"], car_data["position_z"]])
        direction = np.array([car_data["direction_x"], car_data["direction_y"], car_data["direction_z"]])
        rotation = np.array([car_data["rotation_x"], car_data["rotation_y"], car_data["rotation_z"]])
        
        self.tire_FL.resetTransform()
        self.tire_FL.translate(position[0], position[1], position[2])
        
        self.tire_FR.resetTransform()
        self.tire_FR.translate(position[0], position[1], position[2])
        
        self.tire_RL.resetTransform()
        self.tire_RL.translate(position[0], position[1], position[2])
        
        self.tire_RR.resetTransform()
        self.tire_RR.translate(position[0], position[1], position[2])
        
    def toggle_camera_mode(self):
        self.camera_mode += 1
        if self.camera_mode > 3:
            self.camera_mode = 1
    
    def update_camera(self, car_data):
        car_pos = np.array([car_data["position_x"], car_data["position_y"], car_data["position_z"]])
        car_dir = np.arctan2(car_data["direction_y"], car_data["direction_x"]) * 180 / np.pi

        if self.camera_mode == 1:
            dis = self.camera_zoom
            ele = self.camera_angle
        elif self.camera_mode == 2:
            dis = self.camera_zoom
            ele = self.camera_angle
        elif self.camera_mode == 3:
            dis = 10
            ele = 90
            car_dir = 0
        self.w.setCameraPosition(pos=QVector3D(0, 0, 0 -1.0), distance=dis, elevation=ele, azimuth=car_dir)

    def start(self):
        self.w.show()
        self.app.exec()

from PySide6.QtGui import QPainter, QColor, QFont

class CustomGLViewWidget(gl.GLViewWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tire_temperatures = [0, 0, 0, 0]
        self.show_temp = True
        self.setWindowTitle('CarVis')

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont('Arial', 12))
        if self.show_temp:
            painter.drawText(35, 120, 'FL')
            painter.drawText(self.width() - 55, 120, 'FR')
            painter.drawText(15, self.height() - 135, 'RL')
            painter.drawText(self.width() - 35, self.height() - 135, 'RR')
            painter.drawText(25, 135, f'{int(self.tire_temperatures[0])} °c')
            painter.drawText(self.width() - 65, 135, f'{int(self.tire_temperatures[1])} °c')
            painter.drawText(5, self.height() - 120, f'{int(self.tire_temperatures[2])} °c')
            painter.drawText(self.width() - 45, self.height() - 120, f'{int(self.tire_temperatures[3])} °c')
        painter.end()

    def update_temperatures(self, temps):
        self.tire_temperatures = temps
        self.update()  # This triggers a repaint
