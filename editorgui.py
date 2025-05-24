# TODO: More different settings
# TODO: Applying changes
# TODO: Better configuration
# TODO: Replacing 3-char codes with car names
# TODO: Game folder configuration



from pathlib import WindowsPath, Path
from PySide6 import QtWidgets, QtGui, QtCore
from helpers import models_directory, get_camera_list_from_car, get_fov_from_camera_index


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setCentralWidget(CentralWidget())


class CentralWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout()

        # Car List Dropdown
        self.current_car: str = ""
        car_list_model = QtGui.QStandardItemModel()
        for car in models_directory.iterdir():
            car: WindowsPath
            car_list_model.appendRow(QtGui.QStandardItem(car.name))

        carlist = CarList(car_list_model)

        # Camera Dropdown
        self.camera_list_model = QtGui.QStandardItemModel()
        self.camera_list_dropdown = QtWidgets.QComboBox(placeholderText="<cameras>")
        self.camera_list_dropdown.setModel(self.camera_list_model)

        # Camera Editor
        self.camera_editor = CameraEditor()


        # Dropdown Functionality
        carlist.textActivated.connect(self.car_changed)
        self.car_changed(carlist.currentText())
        self.camera_list_dropdown.currentIndexChanged.connect(self.camera_changed)

        # Setting Layout
        self.layout.addWidget(carlist)
        self.layout.addWidget(self.camera_list_dropdown)
        self.layout.addWidget(self.camera_editor)
        self.setLayout(self.layout)

    @QtCore.Slot(str)
    def car_changed(self, text: str):
        self.current_car = text
        cameras = get_camera_list_from_car(models_directory.joinpath(text))
        self.camera_list_model.clear()

        for camera in cameras:
            self.camera_list_model.appendRow(QtGui.QStandardItem(camera))

        self.camera_list_dropdown.setCurrentIndex(0)

        self.camera_changed(0)

    @QtCore.Slot(int)
    def camera_changed(self, index: int):
        self.camera_editor.set_camera(self.current_car, index)


class CarList(QtWidgets.QComboBox):
    """
    Dropdown list of cars
    """
    def __init__(self, model: QtGui.QStandardItemModel):
        super().__init__()
        self.setModel(model)


class CameraList(QtWidgets.QComboBox):
    """
    Dropdown list of cameras for a single car
    """
    def __init__(self):
        super().__init__()


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
