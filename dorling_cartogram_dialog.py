# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets
from qgsfilewidget import QgsFileWidget

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QDialog

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Compute Dorling Cartogram")
        Dialog.resize(518, 320)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.NoButton)
        self.buttonBox.setObjectName("buttonBox")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(30, 30, 91, 16))
        self.label.setObjectName("label")
        self.PushButtonOk = QtWidgets.QPushButton(Dialog)
        self.PushButtonOk.setGeometry(QtCore.QRect(270, 280, 113, 32))
        self.PushButtonOk.setObjectName("PushButtonOk")
        self.PushButtonCancel = QtWidgets.QPushButton(Dialog)
        self.PushButtonCancel.setGeometry(QtCore.QRect(390, 280, 113, 32))
        self.PushButtonCancel.setObjectName("PushButtonCancel")
        self.comboBoxLayer = QtWidgets.QComboBox(Dialog)
        self.comboBoxLayer.setGeometry(QtCore.QRect(130, 20, 361, 32))
        self.comboBoxLayer.setObjectName("comboBoxLayer")
        self.comboBoxAttribute = QtWidgets.QComboBox(Dialog)
        self.comboBoxAttribute.setGeometry(QtCore.QRect(130, 70, 361, 32))
        self.comboBoxAttribute.setObjectName("comboBoxAttribute")
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(20, 80, 101, 16))
        self.label_2.setObjectName("label_2")
        self.mQgsFileWidgetOutput = QgsFileWidget(Dialog)
        self.mQgsFileWidgetOutput.setGeometry(QtCore.QRect(140, 160, 341, 27))
        self.mQgsFileWidgetOutput.setStorageMode(QgsFileWidget.SaveFile)
        self.mQgsFileWidgetOutput.setObjectName("mQgsFileWidgetOutput")
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setGeometry(QtCore.QRect(20, 170, 101, 16))
        self.label_3.setObjectName("label_3")

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept) # type: ignore
        self.buttonBox.rejected.connect(Dialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label.setText(_translate("Dialog", "Select Layer"))
        self.PushButtonOk.setText(_translate("Dialog", "Ok"))
        self.PushButtonCancel.setText(_translate("Dialog", "Cancel"))
        self.label_2.setText(_translate("Dialog", "Select Attribute"))
        self.label_3.setText(_translate("Dialog", "Output Layer"))

class DorlingCartogramDialog(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)