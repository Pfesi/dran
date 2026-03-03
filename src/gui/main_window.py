# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'MainWindow.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(633, 400)
        font = QtGui.QFont()
        #font.setFamily("Times")#("TeX Gyre Adventor")
        MainWindow.setFont(font)
        icon = QtGui.QIcon()
        # icon.addPixmap(QtGui.QPixmap("../icons/3d bar chart.png"),
                    #    QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.main_window_buttons_hLayout = QtWidgets.QHBoxLayout()
        self.main_window_buttons_hLayout.setObjectName(
            "main_window_buttons_hLayout")
        self.btn_edit_driftscan = QtWidgets.QPushButton(self.centralwidget)
        self.btn_edit_driftscan.setEnabled(True)
        self.btn_edit_driftscan.setToolTip("")
        self.btn_edit_driftscan.setStatusTip("")
        self.btn_edit_driftscan.setObjectName("btn_edit_driftscan")
        self.main_window_buttons_hLayout.addWidget(self.btn_edit_driftscan)
        self.btn_edit_timeseries = QtWidgets.QPushButton(self.centralwidget)
        self.btn_edit_timeseries.setObjectName("btn_edit_timeseries")
        self.main_window_buttons_hLayout.addWidget(self.btn_edit_timeseries)
        self.btn_view_plots = QtWidgets.QPushButton(self.centralwidget)
        self.btn_view_plots.setObjectName("btn_view_plots")
        self.main_window_buttons_hLayout.addWidget(self.btn_view_plots)
        self.horizontalLayout.addLayout(self.main_window_buttons_hLayout)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "DRAN"))
        self.btn_edit_driftscan.setText(
            _translate("MainWindow", "Edit Driftscan"))
        self.btn_edit_timeseries.setText(
            _translate("MainWindow", "Edit Time series"))
        self.btn_view_plots.setText(_translate("MainWindow", "View Plots"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    # sys.exit(app.exec_())
