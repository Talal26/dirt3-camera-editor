from os import PathLike

from helpers import iter_cam_files, Cameras
from xml.etree import ElementTree as ET


def camera_mod(camera_file: str | PathLike[str]) -> None:
    tree = ET.parse(camera_file)
    root = tree.getroot()

    for camera in root.find("ViewManager"):
        if camera.get("ident") in [Cameras.BONNET2, Cameras.CHASE_CLOSE, Cameras.COCKPIT]:
            camera.set("hidden", "false")
        else:
            camera.set("hidden", "true")

    tree.write(camera_file, xml_declaration=True, encoding="UTF-8")


for cam_file in iter_cam_files():
    try:
        camera_mod(cam_file)
    except Exception as e:
        print(f"Encountered error converting file: {cam_file}")
        print(e)
    else:
        print(f"Succesfully converted file {cam_file}")
