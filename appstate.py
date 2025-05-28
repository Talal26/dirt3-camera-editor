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
    save_successful = QtCore.Signal()

    def __init__(self, dataframe: pd.DataFrame, config: dict[str, typing.Any]):
        super().__init__()
        self.df = dataframe
        self.models_directory = Path(config["game_install_location"]).joinpath("cars", "models")

        self.parameter_config: dict = config["camera_parameters"]

        self.disciplines = self.df["Discipline"].unique()
        self.current_discipline = 0

        self.current_class = 0

        self.current_car_index = 0

        self.tree = self.fetch_cameras()

        self.current_camera = 0

        self.params = self.fetch_params()

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
        self.current_car_index = index
        self.refresh_car_selection.emit()
        self.change_camera(0)
        self.tree = self.fetch_cameras()
        self.refresh_camera_selection.emit()
        self.params = self.fetch_params()
        self.refresh_params.emit()

        self.edited = False

    @QtCore.Slot(int)
    def change_camera(self, index: int):
        self.current_camera = index
        self.refresh_params.emit()

    @QtCore.Slot(dict)
    def edit_param(self, param_name: str, value: str):
        self.edited = True

        self.params[self.current_camera][param_name]["value"] = value

        self.refresh_params.emit()

    @property
    def classes(self):
        return self.df[self.df["Discipline"] == self.disciplines[self.current_discipline]]["Class"].unique()

    @property
    def cars(self):
        return self.df[self.df["Class"] == self.classes[self.current_class]]

    @property
    def current_car_code(self):
        return self.cars.iloc[self.current_car_index]["Code"]

    @property
    def current_car(self):
        return self.cars.iloc[self.current_car_index]

    @property
    def cameras(self) -> ET.Element:
        root = self.tree.getroot()
        return root.find("ViewManager")

    def fetch_cameras(self) -> ET:
        logging.debug(f"fetching camera information for {self.current_car_code}")

        return ET.parse(self.file_path)

    def fetch_params(self) -> dict[int, dict]:
        params = {}
        for index, camera in enumerate(self.cameras):
            camera_dict = {}

            for key, value in self.parameter_config.items():
                parameter_dict = {}
                try:
                    element = camera.find(value)
                    parameter_type = element.get("type")
                except AttributeError:  # Parameter is not present in this camera
                    continue

                parameter_dict["type"] = parameter_type
                match parameter_type:
                    case "scalar":
                        parameter_dict["value"] = element.get("value")
                    case "bool":
                        parameter_dict["value"] = element.get("value")
                    case "vector3":
                        parameter_dict["x"] = element.get("x")
                        parameter_dict["y"] = element.get("y")
                        parameter_dict["z"] = element.get("z")

                camera_dict[key] = parameter_dict

            params[index] = camera_dict

        return params

    @property
    def file_path(self) -> Path:
        return self.models_directory.joinpath(self.current_car_code, "cameras.xml")

    @QtCore.Slot(dict)
    def save(self):
        logging.debug(f"saving for car code: {self.current_car_code}")

        # Modify tree
        for index, camera in enumerate(self.cameras):
            for parameter, value in self.params[index].items():
                element = camera.find(self.parameter_config[parameter])
                element.set("value", value["value"])

        self.tree.write(self.file_path, xml_declaration=True, encoding="UTF-8")

        self.save_successful.emit()

    def close(self):
        self.close_application.emit()
