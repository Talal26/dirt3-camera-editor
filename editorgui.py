# TODO: More camera params
# TODO: Applying changes
# TODO: Game folder configuration
# TODO: ego file conversion
# TODO: Backups
# TODO: Adding roof cameras

import tomllib
from pathlib import Path

import pandas as pd
from PySide6 import QtWidgets, QtGui, QtCore

from helpers import get_camera_list_from_car, get_fov_from_camera_index

with open("config.toml", "rb") as f:
    config = tomllib.load(f)

game_install_location = config["game_install_location"]
models_directory = Path(game_install_location).joinpath("cars", "models")

df = pd.read_csv("Cars.csv")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DiRT 3 Camera Editor")
        self.setCentralWidget(CentralWidget())
        self.setMinimumWidth(300)


class CentralWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout()

        # Car Selector
        car_selector = CarSelector()
        car_selector.car_selected.connect(self.car_changed)

        # Car List Dropdown
        self.current_car: str = ""

        # Camera Dropdown
        self.camera_list_model = QtGui.QStandardItemModel()
        self.camera_list_dropdown = QtWidgets.QComboBox(placeholderText="<cameras>")
        self.camera_list_dropdown.setModel(self.camera_list_model)

        # Camera Editor
        self.camera_editor = CameraEditor()

        # Dropdown Functionality
        self.camera_list_dropdown.currentIndexChanged.connect(self.camera_changed)

        # Setting Layout
        self.layout.addWidget(car_selector)
        self.layout.addWidget(self.camera_list_dropdown)
        self.layout.addWidget(self.camera_editor)
        self.setLayout(self.layout)

        car_selector.trigger_signal(0)  # Manual trigger otherwise camera params won't load before car is changed once

    @QtCore.Slot(str)
    def car_changed(self, code: str):
        self.current_car = code
        cameras = get_camera_list_from_car(models_directory.joinpath(code))
        self.camera_list_model.clear()

        for camera in cameras:
            self.camera_list_model.appendRow(QtGui.QStandardItem(camera))

        self.camera_list_dropdown.setCurrentIndex(0)

        self.camera_changed(0)

    @QtCore.Slot(int)
    def camera_changed(self, index: int):
        self.camera_editor.set_camera(self.current_car, index)


class CarSelector(QtWidgets.QGroupBox):
    """
    Contains dropdown menus for discpline, car class, and specific cars
    Emits signal when car selection is changed
    """

    car_selected = QtCore.Signal(str)

    def __init__(self):
        super().__init__()

        self.setTitle("Select Car")

        # Discpline Dropdown
        disciplines = df["Discipline"].unique()

        self.discipline_model = QtGui.QStandardItemModel()
        for discipline in disciplines:
            self.discipline_model.appendRow(QtGui.QStandardItem(discipline))

        self.discipline_dropdown = QtWidgets.QComboBox()
        self.discipline_dropdown.setModel(self.discipline_model)

        self.discipline_dropdown.currentTextChanged.connect(self.set_classes)

        # Car Class Dropdown
        self.classes_model = QtGui.QStandardItemModel()
        self.classes_dropdown = QtWidgets.QComboBox()
        self.classes_dropdown.setModel(self.classes_model)

        self.classes_dropdown.currentTextChanged.connect(self.set_cars)

        # Car Dropdown
        self.cars: pd.DataFrame | None = None
        self.cars_model = QtGui.QStandardItemModel()
        self.cars_dropdown = QtWidgets.QComboBox()
        self.cars_dropdown.setModel(self.cars_model)

        self.cars_dropdown.currentIndexChanged.connect(self.trigger_signal)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.discipline_dropdown)
        layout.addWidget(self.classes_dropdown)
        layout.addWidget(self.cars_dropdown)

        self.setLayout(layout)

        # Setup steps
        self.set_classes(self.discipline_dropdown.currentText())
        self.set_cars(self.classes_dropdown.currentText())


    @QtCore.Slot(str)
    def set_classes(self, current_discipline: str) -> None:
        """Sets list of car classes in dropdown based on currently selected discipline"""
        self.classes_dropdown.blockSignals(True)  # Signal blocked to prevent emitting everytime model changes

        self.classes_model.clear()
        for car_class in df[df["Discipline"]  == current_discipline]["Class"].unique():
            self.classes_model.appendRow(QtGui.QStandardItem(car_class))
        self.classes_dropdown.blockSignals(False)
        self.classes_dropdown.currentTextChanged.emit(self.classes_dropdown.currentText())

    @QtCore.Slot(str)
    def set_cars(self, current_class: str) -> None:
        """Sets list of cars in dropdown based on currently selected car class"""
        self.cars_dropdown.blockSignals(True)  # Signal blocked to prevent emitting everytime model changes

        self.cars_model.clear()
        self.cars = df[df["Class"] == current_class]
        for index, car in self.cars.iterrows():
            self.cars_model.appendRow(QtGui.QStandardItem(car["Name"]))

        self.cars_dropdown.blockSignals(False)
        self.cars_dropdown.currentIndexChanged.emit(0)

    def trigger_signal(self, car_index: int) -> None:
        """Triggers the car_selected signal"""

        self.car_selected.emit(self.cars.iloc[car_index]["Code"])


class CameraEditor(QtWidgets.QGroupBox):
    """
    Widget containing fields to edit the camera parameters
    """
    def __init__(self):
        super().__init__()

        self.setTitle("Camera Parameters")

        self.fov_field = QtWidgets.QLineEdit("Undefined", self)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.fov_field)

        self.setLayout(layout)

    @QtCore.Slot(str, int)
    def set_camera(self, car: str, index: int):
        fov = get_fov_from_camera_index(models_directory.joinpath(car), index)
        self.fov_field.setText(str(fov))


def main():
    app = QtWidgets.QApplication()

    window = MainWindow()
    window.show()
    exit(app.exec())


if __name__ == '__main__':
    main()
