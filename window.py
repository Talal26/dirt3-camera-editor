from PySide6 import QtWidgets

from appstate import AppState
from widgets import CentralWidget


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, state: AppState):
        super().__init__()

        self.state = state

        self.state.close_application.connect(self.close)
        self.state.save_successful.connect(self.save_successful_popup)
        self.state.save_unsuccessful.connect(self.save_unsuccesful_popup)

        self.setWindowTitle("DiRT 3 Camera Editor")
        self.setCentralWidget(CentralWidget(self.state))
        self.setMinimumWidth(300)

    def save_successful_popup(self):
        QtWidgets.QMessageBox.information(
            self,
            "Save Succesful!",
            f"Successfully saved changes for {self.state.current_car["Name"]}"
        )

    def save_unsuccesful_popup(self, error: Exception):
        QtWidgets.QMessageBox.critical(
            self,
            "Error saving",
            f"Failed to save changes for car {self.state.current_car["Name"]}\n{error}"
        )
