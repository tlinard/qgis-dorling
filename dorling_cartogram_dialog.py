from PyQt5 import QtWidgets
from .dorling_cartogram_dialog_base import Ui_Dialog

class DorlingCartogramDialog(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)