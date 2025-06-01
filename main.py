# TODO: More camera params
# TODO: Game folder configuration
# TODO: ego file conversion
# TODO: Backups
# TODO: Adding roof cameras
# TODO: Unsaved changes pop-up window
# TODO: Handling for if unknown car is in game files or car doesn't have cameras.xml file
# TODO: Human-friendly names for cameras, and maybe car classes

import logging
import tomllib

import pandas as pd
from PySide6 import QtWidgets

from appstate import AppState
from window import MainWindow

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(message)s")


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
