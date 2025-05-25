# TODO: More camera params
# TODO: Game folder configuration
# TODO: ego file conversion
# TODO: Backups
# TODO: Adding roof cameras

import logging
import tomllib
import typing
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd
from PySide6 import QtWidgets, QtGui, QtCore

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")


class AppState(QtCore.QObject):
    refresh_car_selection = QtCore.Signal()
    refresh_camera_selection = QtCore.Signal()
    refresh_params = QtCore.Signal()

    close_application = QtCore.Signal()

    def __init__(self, dataframe: pd.DataFrame, config: dict[str, typing.Any]):
        super().__init__()
        self.df = dataframe
        self.models_directory = Path(config["game_install_location"]).joinpath("cars", "models")

        self.camera_parameters: dict = config["camera_parameters"]

        self.disciplines = self.df["Discipline"].unique()
        self.current_discipline = 0

        self.current_class = 0

        self.current_car = 0

        self.tree = ET.parse(self.file_path)

        self.current_camera = 0

        self.edited = False

    @QtCore.Slot(int)
    def change_discipline(self, index: int):
        self.current_discipline = index
        self.change_class(0)

    @QtCore.Slot(int)
    def change_class(self, index: int):
        self.current_class = index
        self.change_car(0)

    @QtCore.Slot(int)
    def change_car(self, index: int):
        self.current_car = index
        self.refresh_car_selection.emit()
        self.change_camera(0)
        self.fetch_cameras()
        self.refresh_camera_selection.emit()
        self.refresh_params.emit()

        self.edited = False

    @QtCore.Slot(int)
    def change_camera(self, index: int):
        self.current_camera = index
        self.refresh_params.emit()

    @QtCore.Slot(dict)
    def edit_params(self, params: dict):
        self.edited = True

        for key, value in params.items():
            self.cameras[self.current_camera].find(f".//Parameter[@name='{key}']").set("value", value)

        self.refresh_params.emit()

    @property
    def classes(self):
        return self.df[self.df["Discipline"] == self.disciplines[self.current_discipline]]["Class"].unique()

    @property
    def cars(self):
        return self.df[self.df["Class"] == self.classes[self.current_class]]

    @property
    def current_car_code(self):
        return self.cars.iloc[self.current_car]["Code"]

    @property
    def cameras(self) -> ET.Element:
        root = self.tree.getroot()
        return root.find("ViewManager")

    def fetch_cameras(self) -> None:
        logging.debug(f"fetching camera information for {self.current_car_code}")

        self.tree = ET.parse(self.file_path)

    @property
    def params(self) -> dict:
        params = {}
        for key, value in self.camera_parameters.items():
            try:
                params[key] = self.cameras[self.current_camera].find(value).get("value")
            except AttributeError:
                pass
        return params

    @property
    def file_path(self) -> Path:
        return self.models_directory.joinpath(self.current_car_code, "cameras.xml")

    @QtCore.Slot(dict)
    def save(self):
        logging.debug(f"saving for car code: {self.current_car_code}")

        self.tree.write(self.file_path, xml_declaration=True, encoding="UTF-8")

    def close(self):
        self.close_application.emit()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, state: AppState):
        super().__init__()

        state.close_application.connect(self.close)

        self.setWindowTitle("DiRT 3 Camera Editor")
        self.setCentralWidget(CentralWidget(state))
        self.setMinimumWidth(300)


class CentralWidget(QtWidgets.QWidget):
    def __init__(self, state: AppState):
        super().__init__()

        self.state = state

        self.layout = QtWidgets.QVBoxLayout()

        # Car Selector
        car_selector = CarSelector(self.state)

        # Car List Dropdown
        self.current_car: str = ""

        # Camera List Dropdown
        self.camera_selector = CameraSelector(state)

        # Camera Editor
        self.camera_editor = CameraEditor(self.state)

        # Button Row
        self.button_row = ButtonRow(self.state)
        self.button_row.save_clicked.connect(self.state.save)

        # Setting Layout
        self.layout.addWidget(car_selector)
        self.layout.addWidget(self.camera_selector)
        self.layout.addWidget(self.camera_editor)
        self.layout.addWidget(self.button_row)
        self.setLayout(self.layout)


class CarSelector(QtWidgets.QGroupBox):
    """
    Contains dropdown menus for discpline, car class, and specific cars
    Emits signal when car selection is changed
    """

    def __init__(self, state: AppState):
        super().__init__()

        self.state = state
        self.state.refresh_car_selection.connect(self.refresh)

        self.setTitle("Select Car")

        # Discpline Dropdown
        disciplines = self.state.disciplines

        self.discipline_model = QtGui.QStandardItemModel()
        for discipline in disciplines:
            self.discipline_model.appendRow(QtGui.QStandardItem(discipline))

        self.discipline_dropdown = QtWidgets.QComboBox()
        self.discipline_dropdown.setModel(self.discipline_model)

        self.discipline_dropdown.currentIndexChanged.connect(self.state.change_discipline)

        # Car Class Dropdown
        self.classes_model = QtGui.QStandardItemModel()
        self.classes_dropdown = QtWidgets.QComboBox()
        self.classes_dropdown.setModel(self.classes_model)

        self.classes_dropdown.currentIndexChanged.connect(self.state.change_class)

        # Car Dropdown
        self.cars: pd.DataFrame | None = None
        self.cars_model = QtGui.QStandardItemModel()
        self.cars_dropdown = QtWidgets.QComboBox()
        self.cars_dropdown.setModel(self.cars_model)

        self.cars_dropdown.currentIndexChanged.connect(self.state.change_car)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.discipline_dropdown)
        layout.addWidget(self.classes_dropdown)
        layout.addWidget(self.cars_dropdown)

        self.setLayout(layout)

        self.refresh()


    @QtCore.Slot()
    def refresh(self):
        self.classes_dropdown.blockSignals(True)
        self.cars_dropdown.blockSignals(True)

        self.discipline_dropdown.setCurrentIndex(self.state.current_discipline)

        self.classes_model.clear()
        for car_class in self.state.classes:
            self.classes_model.appendRow(QtGui.QStandardItem(car_class))

        self.classes_dropdown.setCurrentIndex(self.state.current_class)

        self.cars_model.clear()
        for car in self.state.cars["Name"]:
            self.cars_model.appendRow(QtGui.QStandardItem(car))

        self.cars_dropdown.setCurrentIndex(self.state.current_car)

        self.classes_dropdown.blockSignals(False)
        self.cars_dropdown.blockSignals(False)


class CameraSelector(QtWidgets.QGroupBox):
    """
    Contains dropdown selector for camera
    """
    def __init__(self, state: AppState):
        super().__init__()

        self.state = state
        self.state.refresh_camera_selection.connect(self.refresh)

        self.setTitle("Select Camera")

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.model = QtGui.QStandardItemModel()
        self.dropdown = QtWidgets.QComboBox()
        self.dropdown.setModel(self.model)

        for camera in self.state.cameras:
            self.model.appendRow(QtGui.QStandardItem(camera.get("ident")))

        self.dropdown.currentIndexChanged.connect(self.state.change_camera)

        layout.addWidget(self.dropdown)

    @QtCore.Slot()
    def refresh(self):
        self.dropdown.blockSignals(True)
        self.model.clear()
        for camera in self.state.cameras:
            self.model.appendRow(QtGui.QStandardItem(camera.get("ident")))

        self.dropdown.setCurrentIndex(self.state.current_camera)

        self.dropdown.blockSignals(False)


class CameraEditor(QtWidgets.QGroupBox):
    """
    Widget containing fields to edit the camera parameters
    """
    def __init__(self, state: AppState):
        super().__init__()

        self.state = state
        self.state.refresh_params.connect(self.refresh)

        layout = QtWidgets.QVBoxLayout()
        self.setTitle("Camera Parameters")

        for key, value in self.state.params.items():
            sublayout = QtWidgets.QHBoxLayout()

            label = QtWidgets.QLabel(f"{key}:", self)

            field = QtWidgets.QLineEdit(value, self)
            field.setObjectName(key)
            field.editingFinished.connect(self.edit_params)

            sublayout.addWidget(label)
            sublayout.addWidget(field)

            layout.addLayout(sublayout)

        self.setLayout(layout)

    def refresh(self):
        for key, value in self.state.params.items():
            field = self.findChild(QtWidgets.QLineEdit, key)
            field.setText(value)

    def edit_params(self):
        logging.debug("edit_params ran")

        params = {}
        for child in self.findChildren(QtWidgets.QLineEdit):
            params[child.objectName()] = child.text()

        self.state.edit_params(params)


class ButtonRow(QtWidgets.QWidget):
    save_clicked = QtCore.Signal()
    close_clicked = QtCore.Signal()

    def __init__(self, state: AppState):
        super().__init__()

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        save_button = QtWidgets.QPushButton("Save", self)
        save_button.clicked.connect(self.save_clicked)

        close_button = QtWidgets.QPushButton("Close", self)
        close_button.clicked.connect(state.close)

        layout.addWidget(save_button)
        layout.addWidget(close_button)


def main():
    app = QtWidgets.QApplication()

    df = pd.read_csv("Cars.csv")
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)

    state = AppState(df, config)

    window = MainWindow(state)
    window.show()
    exit(app.exec())


if __name__ == '__main__':
    main()
