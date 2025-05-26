import logging
import typing
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd
from PySide6 import QtCore


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
