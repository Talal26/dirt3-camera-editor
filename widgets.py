import logging

import pandas as pd
from PySide6 import QtWidgets, QtGui, QtCore

from appstate import AppState


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

        self.cars_dropdown.setCurrentIndex(self.state.current_car_index)

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

        self.layout = QtWidgets.QVBoxLayout()
        self.setTitle("Camera Parameters")

        self.widgets = {}

        for key, value in self.state.params[self.state.current_camera].items():
            self.create_field(key, value["value"])

        self.setLayout(self.layout)

    def refresh(self):
        # Create or enable widget for each paramater for this camera
        for widget in self.widgets.values():
            widget.hide()

        for key,value in self.state.params[self.state.current_camera].items():
            param_name = key
            param_type = value["type"]
            param_value = value["value"]

            # First check if layout exists
            if param_name not in self.widgets:
                self.create_field(param_name, param_value)

            widget = self.widgets[param_name]
            widget.show()
            widget.set_value(param_value)

    def create_field(self, param_name: str, param_value: str):
        widget = ParameterField(param_name, param_value, self)
        self.layout.addWidget(widget)
        self.widgets[param_name] = widget

        widget.editingFinished.connect(self.edit_params)


    def edit_params(self, param_name: str, value: str):
        logging.debug(f"params edited: {param_name} = {value}")

        self.state.edit_param(param_name, value)
        self.state.params[self.state.current_camera][param_name]["value"] = value


class ParameterField(QtWidgets.QWidget):
    editingFinished = QtCore.Signal(str, str)

    def __init__(self, param_name: str, initial_value: str = "", parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)

        self.param_name = param_name

        layout = QtWidgets.QHBoxLayout()

        label = QtWidgets.QLabel(f"{param_name}:", self)

        self.field = QtWidgets.QLineEdit(initial_value, self)
        self.field.editingFinished.connect(self.send_signal)

        layout.addWidget(label)
        layout.addWidget(self.field)

        self.setLayout(layout)

    def set_value(self, value: str):
        self.field.setText(value)

    def send_signal(self):
        self.editingFinished.emit(self.param_name, self.field.text())


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
