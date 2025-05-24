from enum import StrEnum
from pathlib import Path, WindowsPath
from typing import Generator
from xml.etree import ElementTree as ET

models_directory = Path(r"D:\SteamLibrary\steamapps\common\DiRT 3 Complete Edition\cars\models")


class Cameras(StrEnum):
    CHASE_CLOSE = "chase_close"
    CHASE_CLOSE_REVERSE = "chase_close_reverse"
    CHASE_FAR = "chase_far"
    CHASE_FAR_REVERSE = "chase_far_reverse"
    BUMPER = "bumper"
    BUMPER_REVERSE = "bumper_reverse"
    BONNET = "bonnet"
    BONNET_REVERSE = "bonnet_reverse"
    BONNET2 = "bonnet2"
    ROOF_REVERSE = "roof_reverse"
    COCKPIT = "head-cam"
    COCKPIT_REVERSE = "head-cam_reverse"
    REPLAY_WHEEL1 = "replay_wheel1"
    REPLAY_WHEEL2 = "replay_wheel2"
    REPLAY_WING1 = "replay_wing1"
    REPLAY_WING2 = "replay_wing2"
    REPLAY_HOOD1 = "replay_hood1"
    REPLAY_HOOD2 = "replay_hood2"
    REPLAY_DRIVER1 = "replay_driver1"
    REPLAY_DRIVER2 = "replay_driver2"


def iter_cam_files() -> Generator[WindowsPath]:
    for car in models_directory.iterdir():
        camera_file = car.joinpath("cameras.xml")
        if camera_file.exists():
            yield camera_file


def get_camera_list_from_car(car: str) -> list[str]:
    """
    Returns list of camera idents for a single car
    :param car: Directory of the car (including cars/model)
    :return: full list of camera idents in the car
    """
    camera_file = Path(car).joinpath("cameras.xml")

    tree = ET.parse(camera_file)
    root = tree.getroot()

    return [camera.get("ident") for camera in root.find("ViewManager")]


def get_fov_from_camera_index(car: str, index: int) -> float:
    camera_file = Path(car).joinpath("cameras.xml")
    tree = ET.parse(camera_file)
    root = tree.getroot()

    return root.find("ViewManager")[index].find(".//Parameter[@name='fov']").get("value")
