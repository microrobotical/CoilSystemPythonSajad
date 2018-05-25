from PyQt5 import uic
from PyQt5.QtCore import QFile, QRegExp, QTimer, Qt, pyqtSlot
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QMenu, QMessageBox
from fieldManager import FieldManager
from vision import Vision
from s826 import S826
from subThread import SubThread
from realTimePlot import CustomFigCanvas
from mathfx import *
import syntax
#=========================================================
# UI Config
#=========================================================
qtCreatorFile = "mainwindow.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
#=========================================================
# Creating instances of fieldManager and Camera
#=========================================================
field = FieldManager(S826())
vision = Vision(index=1,type='firewire',guid=2672909588927744,buffersize=10) # greyscale mode
# vision2 = Vision(index=2,type='firewire',guid=2672909587849792  ,buffersize=4)
# to use usb camera, try    vision = Vision(index=1,type='usb')
# to use 1 camera only, comment out this line:    vision2 = ...
#=========================================================
# a class that handles the signal and callbacks of the GUI
#=========================================================
class GUI(QMainWindow,Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self,None,Qt.WindowStaysOnTopHint)
        Ui_MainWindow.__init__(self)
        self.updateRate = 15 # (ms) update rate of the GUI, vision, plot
        self.setupUi(self)
        self.setupTimer()
        self.setupSubThread(field,vision)
        self.setupRealTimePlot() # comment ou this line if you don't want a preview window
        self.connectSignals()
        self.linkWidgets()

    #=====================================================
    # [override] terminate the subThread and clear currents when closing the window
    #=====================================================
    def closeEvent(self,event):
        self.thrd.stop()
        self.timer.stop()
        vision.cam.stop_video()
        try:
            vision2
        except NameError:
            pass
        else:
            vision2.cam.stop_video()
        self.clearField()
        event.accept()

    #=====================================================
    # QTimer handles updates of the GUI, run at 60Hz
    #=====================================================
    def setupTimer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.updateRate) # msec

    def update(self):
        vision.updateFrame()
        try:
            vision2
        except NameError:
            pass
        else:
            vision2.updateFrame()
        try:
            self.realTimePlot
        except AttributeError:
            pass
        else:
            self.updatePlot()

    #=====================================================
    # Connect buttons etc. of the GUI to callback functions
    #=====================================================
    def connectSignals(self):
        # XYZ Mode Tab
        self.dsb_x.valueChanged.connect(self.setField)
        self.dsb_y.valueChanged.connect(self.setField)
        self.dsb_z.valueChanged.connect(self.setField)
        self.dsb_pxpx.valueChanged.connect(self.setField)
        self.dsb_pxpy.valueChanged.connect(self.setField)
        self.dsb_pxpz.valueChanged.connect(self.setField)
        self.dsb_pypy.valueChanged.connect(self.setField)
        self.dsb_pypz.valueChanged.connect(self.setField)
        self.btn_clearCurrent.clicked.connect(self.clearField)
        # Angle Mode Tab
        self.dsb_mag.valueChanged.connect(self.setFieldByAngle)
        self.dsb_azimuth.valueChanged.connect(self.setFieldByAngle)
        self.dsb_polar.valueChanged.connect(self.setFieldByAngle)
        # Vision Tab
        self.highlighter = syntax.Highlighter(self.editor_vision.document())
        self.chb_bypassFilters.toggled.connect(self.on_chb_bypassFilters)
        self.chb_startPauseCapture.toggled.connect(self.on_chb_startPauseCapture)
        self.btn_refreshFilterRouting.clicked.connect(self.on_btn_refreshFilterRouting)
        # object detection
        self.chb_objectDetection.toggled.connect(self.on_chb_objectDetection)
        # Subthread Tab
        self.cbb_subThread.currentTextChanged.connect(self.on_cbb_subThread)
        self.chb_startStopSubthread.toggled.connect(self.on_chb_startStopSubthread)
        self.dsb_subThreadParam0.valueChanged.connect(self.thrd.setParam0)
        self.dsb_subThreadParam1.valueChanged.connect(self.thrd.setParam1)
        self.dsb_subThreadParam2.valueChanged.connect(self.thrd.setParam2)
        self.dsb_subThreadParam3.valueChanged.connect(self.thrd.setParam3)
        self.dsb_subThreadParam4.valueChanged.connect(self.thrd.setParam4)


    #=====================================================
    # Link GUI elements
    #=====================================================
    def linkWidgets(self):
        # XYZ Mode
        self.dsb_x.valueChanged.connect(lambda value: self.hsld_x.setValue(int(value*100)))
        self.dsb_y.valueChanged.connect(lambda value: self.hsld_y.setValue(int(value*100)))
        self.dsb_z.valueChanged.connect(lambda value: self.hsld_z.setValue(int(value*100)))
        self.hsld_x.valueChanged.connect(lambda value: self.dsb_x.setValue(float(value/100)))
        self.hsld_y.valueChanged.connect(lambda value: self.dsb_y.setValue(float(value/100)))
        self.hsld_z.valueChanged.connect(lambda value: self.dsb_z.setValue(float(value/100)))

        # Angle Mode
        self.dsb_mag.valueChanged.connect(lambda value: self.hsld_mag.setValue(int(value*100)))
        self.dsb_azimuth.valueChanged.connect(lambda value: self.hsld_azimuth.setValue(int(value*10)))
        self.dsb_polar.valueChanged.connect(lambda value: self.hsld_polar.setValue(int(value*10)))
        self.hsld_mag.valueChanged.connect(lambda value: self.dsb_mag.setValue(float(value/100)))
        self.hsld_azimuth.valueChanged.connect(lambda value: self.dsb_azimuth.setValue(float(value/10)))
        self.hsld_polar.valueChanged.connect(lambda value: self.dsb_polar.setValue(float(value/10)))

    #=====================================================
    # Thread Example
    #=====================================================
    def setupSubThread(self,field,vision):
        self.thrd = SubThread(field,vision)
        self.thrd.statusSignal.connect(self.updateSubThreadStatus)
        self.thrd.finished.connect(self.finishSubThreadProcess)

    # updating GUI according to the status of the subthread
    @pyqtSlot(str)
    def updateSubThreadStatus(self, receivedStr):
        print('Received message from subthread: ',receivedStr)
        # show something on GUI

    # run when the subthread is termianted
    @pyqtSlot()
    def finishSubThreadProcess(self):
        print('Subthread is terminated.')
        self.clearField()
        # disable some buttons etc.

    #=====================================================
    # Real time plot
    # This is showing actual coil current that is stored in field.x, field.y, field.z
    # Note: the figure is updating at the speed of self.updateRate defined in _init_
    #=====================================================
    def setupRealTimePlot(self):
        self.realTimePlot = CustomFigCanvas()
        self.LAYOUT_A.addWidget(self.realTimePlot, *(0,0)) # put the preview window in the layout
        self.btn_zoom.clicked.connect(self.realTimePlot.zoom) # connect qt signal to zoom funcion

    def updatePlot(self):
        self.realTimePlot.addDataX(field.vecField[0])
        self.realTimePlot.addDataY(field.vecField[1])
        self.realTimePlot.addDataZ(field.vecField[2])

    #=====================================================
    # Callback Functions
    #=====================================================
    # general field Control
    def setField(self):
        ''' XYZ Mode '''
        field.setField([
            self.dsb_x.value(),self.dsb_y.value(),self.dsb_z.value(),
            self.dsb_pxpx.value(),self.dsb_pxpy.value(),self.dsb_pxpz.value(),self.dsb_pypy.value(),self.dsb_pypz.value()
            ])

    def setFieldByAngle(self):
        ''' Angle Mode. No gradient. '''
        magnitude = self.dsb_mag.value()
        azimuth = self.dsb_azimuth.value()
        polar = self.dsb_polar.value()
        fieldX = magnitude * cosd(polar) * cosd(azimuth)
        fieldY = magnitude * cosd(polar) * sind(azimuth)
        fieldZ = magnitude * sind(polar)
        print(fieldX,fieldY,fieldZ)
        field.setField([fieldX,fieldY,fieldZ,0,0,0,0,0])

    def clearField(self):
        field.setField([0,0,0,0,0,0,0,0])
        self.dsb_x.setValue(0)
        self.dsb_y.setValue(0)
        self.dsb_z.setValue(0)
        self.dsb_pxpx.setValue(0)
        self.dsb_pxpy.setValue(0)
        self.dsb_pxpz.setValue(0)
        self.dsb_pypy.setValue(0)
        self.dsb_pypz.setValue(0)
        self.dsb_mag.setValue(0)
        self.dsb_azimuth.setValue(0)
        self.dsb_polar.setValue(0)

    # vision tab
    def on_chb_bypassFilters(self,state):
        vision.setStateFiltersBypassed(state)

    def on_chb_startPauseCapture(self,state):
        vision.setStateUpdate(state)

    def on_btn_refreshFilterRouting(self):
        vision.createFilterRouting(self.editor_vision.toPlainText().splitlines())

    def on_chb_objectDetection(self,state):
        algorithm = self.cbb_objectDetectionAlgorithm.currentText()
        vision.setStateObjectDetection(state,algorithm)
        self.cbb_objectDetectionAlgorithm.setEnabled(not state)

    # subthread
    def on_cbb_subThread(self,subThreadName):
        # an array that stores the name for params. Return param0, param1, ... if not defined.
        labelNames = self.thrd.labelOnGui.get(subThreadName,self.thrd.labelOnGui['default'])
        minVals = self.thrd.minOnGui.get(subThreadName,self.thrd.minOnGui['default'])
        maxVals = self.thrd.maxOnGui.get(subThreadName,self.thrd.maxOnGui['default'])
        defaultVals = self.thrd.defaultValOnGui.get(subThreadName,self.thrd.defaultValOnGui['default'])
        for i in range(5):
            targetLabel = 'lbl_subThreadParam' + str(i)
            targetSpinbox = 'dsb_subThreadParam' + str(i)
            getattr(self,targetLabel).setText(labelNames[i])
            getattr(self,targetSpinbox).setMinimum(minVals[i])
            getattr(self,targetSpinbox).setMaximum(maxVals[i])
            getattr(self,targetSpinbox).setValue(defaultVals[i])


    def on_chb_startStopSubthread(self,state):
        subThreadName = self.cbb_subThread.currentText()
        if state:
            self.cbb_subThread.setEnabled(False)
            self.thrd.setup(subThreadName)
            self.thrd.start()
            print('Subthread "{}" starts.'.format(subThreadName))
        else:
            self.cbb_subThread.setEnabled(True)
            self.thrd.stop()
