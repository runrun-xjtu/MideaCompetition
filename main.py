from PySide2.QtWidgets import QApplication, QMessageBox
from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import QIcon
from PySide2.QtCore import QThread, Signal, Slot, QObject
from socket import *
import pyqtgraph as pg
import math
import re
import requests
import datetime
import time
import _thread
import PID

class Stats(QObject):
    global step, stepLength, stepNum
    global PMV, adjustNum, tRoomNew, tRoomLast
    state = False
    step = 0
    stepNum = 100
    adjustNum = 0

    updateSignal = Signal()

    def __init__(self):
        super(Stats, self).__init__()
        self.ui = QUiLoader().load('main.ui')
        self.ui.deviceButton.buttonClicked.connect(self.deviceChange)
        self.ui.button_test1.clicked.connect(self.valueDefault1)
        self.ui.button_test2.clicked.connect(self.valueDefault2)
        self.ui.button_clear.clicked.connect(self.valueClear)
        self.ui.button_pmv.clicked.connect(self.pmvCalc)
        self.ui.button_test01.clicked.connect(self.weatherUrl1)
        self.ui.button_test02.clicked.connect(self.weatherUrl2)
        self.ui.button_get.clicked.connect(self.weatherGet)
        self.ui.button_clr.clicked.connect(self.weatherClear)
        self.figInit()
        self.ui.button_init.clicked.connect(self.init)
        self.ui.button_begin.clicked.connect(self.begin)
        self.ui.button_stop.clicked.connect(self.stop)
        self.updateSignal.connect(self.progressBarupdate)

    def progressBarupdate(self):
        global step, stepLength, stepNum, p2, curve1, calcTime, calcTem, calcPmv
        self.ui.progressBar.setValue(0)
        if step > 0 and step < stepNum:
            self.ui.progressBar.setValue(int((step - 1) / stepNum * 100.0))
        else:
            self.ui.progressBar.setValue(int(step / stepNum * 100.0))
        curve1.setData(calcTime, calcTem)
        p2.clear()
        p2.addItem(pg.PlotCurveItem(calcTime, calcPmv, pen='b'))
        self.ui.progressBar.update()

    def figInit(self):  # ??????????????????
        self.ui.line_stepNum.setText("120")
        self.ui.line_stepLength.setText("10.0")
        self.ui.line_acCpacity.setText("2.0")
        self.ui.line_lossHeat.setText("0.6")

        self.ui.progressBar.setRange(0, 100)
        self.ui.progressBar.setValue(0)
        graph = pg.GraphicsLayoutWidget()
        self.ui.graphLayout.addWidget(graph)
        graph.setBackground('w')

        global p1, p2

        p1 = graph.addPlot(title="???????????????PMV???????????? ")
        p1.showGrid(x=True, y=False)
        p1.setLogMode(x=False, y=False)
        p1.setLabel('left', text='????????????', color='#000000', units='???')
        p1.setLabel('bottom', text='??????', color='#000000', units='s')
        p1.getAxis('left').setPen('#000000')
        p1.getAxis('bottom').setPen('#000000')
        p1.getAxis('top').setPen('#000000')
        p1.showAxis('top')

        p2 = pg.ViewBox()
        p1.showAxis('right')
        p1.scene().addItem(p2)
        p2.setXLink(p1)
        p1.getAxis('right').setPen('b')
        p1.getAxis('right').linkToView(p2)
        p1.getAxis('right').setLabel('P M V', color='#0000ff')

        p1.setYRange(10, 40)
        p2.setYRange(-3, 3)

        def updateViews():
            global p1, p2
            p2.setGeometry(p1.vb.sceneBoundingRect())
            p2.linkedViewChanged(p1.vb, p2.XAxis)

        updateViews()
        p1.vb.sigResized.connect(updateViews)

        global calcTime, calcTem, calcPmv, curve1, curve2
        calcTime = []
        calcTem = []
        calcPmv = []
        curve1 = p1.plot(calcTime, calcTem, pen='#000000')  # ?????????p??????????????????????????????
        p2.addItem(pg.PlotCurveItem(calcTime, calcPmv, pen='b'))

    def init(self):
        self.ui.button_begin.setText("??????")
        self.ui.button_stop.setText("??????")
        global roomL, roomW, roomH, taInit, trInit, humInit, metInit, workInit, cloInit, pmvInit, pmvMin, pmvMax, compressorSelect, airTemInit
        global calcTime, calcTem, calcPmv, curve1, curve2, stepNum, stepLength, step, state, Qcapacity, hWall
        global adjustNum, tRoomLast, tRoomNew, PMV
        step = 0
        state = False
        calcTime = []
        calcTem = []
        calcPmv = []
        curve1.setData(calcTime, calcTem)
        p2.clear()
        try:
            roomL = float(self.ui.line_roomL.text())
            roomW = float(self.ui.line_roomW.text())
            roomH = float(self.ui.line_roomH.text())

            taInit = float(self.ui.line_ta.text())
            trInit = float(self.ui.line_tr.text())
            humInit = float(self.ui.line_hum.text())
            metInit = float(self.ui.line_met.text())
            workInit = float(self.ui.line_work.text())
            cloSelectInit = self.ui.combo_clo.currentText()  # ???????????? clo    AI????????? ??????????????? ???????????????
            cloInit = 0.5 if cloSelectInit == "?????????-??????" else (
                1.0 if cloSelectInit == "????????????-???" else (1.1 if cloSelectInit == "?????????-??????" else 1.3))
            #pmvInit = float(self.ui.label_resultPmvVal.text())
            pmvMin = float(self.ui.line_pmvMin.text())
            pmvMax = float(self.ui.line_pmvMax.text())
            # airTemInit = float(self.ui.label_airTemMin.text()[:-1])
            compressorSelect = self.ui.combo_frequency.currentText()
            stepNum = int(self.ui.line_stepNum.text())
            stepLength = float(self.ui.line_stepLength.text())
            Qcapacity = float(self.ui.line_acCpacity.text())
            hWall = float(self.ui.line_lossHeat.text())
        except ValueError:
            QMessageBox.information(self.ui, 'Input Error', '??????????????????????????????????????????????????????PMV?????????????????????')
        else:
            self.pmvCalc()
            tRoomLast = taInit
            calcTime.append(0.0 * stepLength)
            calcTem.append(taInit)
            calcPmv.append(PMV)
            curve1.setData(calcTime, calcTem)
            p2.addItem(pg.PlotCurveItem(calcTime, calcPmv, pen='b'))
            self.updateSignal.emit()

    def begin(self):
        global roomL, roomW, roomH, taInit, trInit, humInit, metInit, workInit, cloInit, pmvInit, pmvMin, pmvMax, compressorSelect, airTemInit
        global calcTime, calcTem, calcPmv, curve1, curve2, p2, stepNum, stepLength, step, state, Qcapacity, hWall
        global adjustNum, tRoomLast, tRoomNew, PMV, runState, timeCount, pmvRoom, dQRoom
        state = True
        self.ui.button_begin.setText("-")

        def thread_Simulation(self):
            global roomL, roomW, roomH, taInit, trInit, humInit, metInit, workInit, cloInit, pmvInit, pmvMin, pmvMax, compressorSelect, airTemInit
            global calcTime, calcTem, calcPmv, curve1, curve2, p2, stepNum, stepLength, step, state, Qcapacity, hWall
            global adjustNum, tRoomLast, tRoomNew, PMV, runState, timeCount, pmvRoom, Walltem, dQRoom
            """ ???????????? """
            QStd = 2500.0
            taInStd = 27.0
            taOutStd = 13.0
            trStd = 10.0
            kAStd = 2500.0 / (
                    ((taInStd - trStd) - (taOutStd - trStd)) / (math.log((taInStd - trStd) / (taOutStd - trStd))))
            cpAveStd = 1.0057 + ((1.0069 - 1.0057) / 40) * (0.5 * taInStd + 0.5 * taOutStd)
            denAveStd = 1.2931 + ((1.1274 - 1.2931) / 40) * (0.5 * taInStd + 0.5 * taOutStd)
            VaStd = QStd / (taInStd - taOutStd) / cpAveStd / (1000 * denAveStd)  # ?????? m3/s

            """ ??????????????? """
            Walltem = 35
            controllPeriod = 30 #????????????????????????
            minPowerRatio = 0.25
            if step == 0:
                adjustNum = 0
                timeCount = 0
                tRoomLast = taInit
                runState = 0
            if taInit > 25:
                 Walltem = taInit
            pmvAve = 0.5 * (pmvMin + pmvMax)
            ratio = Qcapacity * 2500 / QStd
            kA = ratio * kAStd
            Va = ratio * VaStd
            VRoom = roomL * roomW * roomH  # ?????? m3

            """ ????????????????????? """
            while step < stepNum:
                if state:
                    step += 1
                    time.sleep(0.1)

                    mRoom = VRoom * (1.2931 + ((1.1274 - 1.2931) / 40) * tRoomLast)  # ?????? kg
                    cpRoom = 1.0057 + ((1.0069 - 1.0057) / 40) * tRoomLast
                    AreaRoom = 2 * (roomL * roomW + roomL * roomH + roomW * roomH)

                    if compressorSelect == "??????":
                        """ ???????????????????????? """
                        taIn = tRoomLast
                        EstiMax = taIn
                        EstiMin = trStd
                        while True:
                            taOutEsti = 0.5 * (EstiMax + EstiMin)
                            cpAve = 1.0057 + ((1.0069 - 1.0057) / 40) * (0.5 * taIn + 0.5 * taOutEsti)
                            denAve = 1.2931 + ((1.1274 - 1.2931) / 40) * (0.5 * taIn + 0.5 * taOutEsti)
                            QEsti1 = Va * (1000 * denAve) * cpAve * (taIn - taOutEsti)
                            QEsti2 = kA * (((taIn - trStd) - (taOutEsti - trStd)) / (
                                math.log((taIn - trStd) / (taOutEsti - trStd))))
                            if math.fabs(QEsti1 - QEsti2) < 1e-6:
                                break
                            else:
                                if QEsti1 > QEsti2:
                                    EstiMax = EstiMax
                                    EstiMin = taOutEsti
                                else:
                                    EstiMax = taOutEsti
                                    EstiMin = EstiMin

                        taOut = taOutEsti  # ?????????????????????
                        QinStep = QEsti1  # ??????????????????
                        timeCount += stepLength
                        if timeCount >= controllPeriod or step == 1:
                            timeCount = 0
                            """ PMV ?????? """
                            judgePeriod = (pmvMax - pmvMin) * math.pow(0.5, adjustNum + 1)
                            self.ui.line_ta.setText(str(round(tRoomLast, 2)))
                            self.ui.line_tr.setText(str(round(tRoomLast - 1, 2)))
                            self.pmvCalc()
                            pmvRoom = PMV
                            """ ??????PMV?????? """
                            if adjustNum % 2 == 0:
                                if pmvRoom > (pmvAve - judgePeriod):
                                    dQRoom = stepLength * (hWall * AreaRoom * (Walltem - tRoomLast) - QinStep)
                                    runState = 1
                                else:
                                    dQRoom = stepLength * (hWall * AreaRoom * (Walltem - tRoomLast))
                                    adjustNum += 1
                                    runState = 2
                            else:
                                if pmvRoom > (pmvAve + judgePeriod):
                                    dQRoom = stepLength * (hWall * AreaRoom * (Walltem - tRoomLast) - QinStep)
                                    adjustNum += 1
                                    runState = 3
                                else:
                                    dQRoom = stepLength * (hWall * AreaRoom * (Walltem - tRoomLast))
                                    runState = 4
                        else:
                            if runState == 1:
                                dQRoom = stepLength * (hWall * AreaRoom * (Walltem - tRoomLast) - QinStep)
                            elif runState == 2:
                                dQRoom = stepLength * (hWall * AreaRoom * (Walltem - tRoomLast))
                            elif runState == 3:
                                dQRoom = stepLength * (hWall * AreaRoom * (Walltem - tRoomLast) - QinStep)
                            elif runState == 4:
                                dQRoom = stepLength * (hWall * AreaRoom * (Walltem - tRoomLast))

                    elif compressorSelect == "??????":
                        timeCount += stepLength
                        if timeCount >= controllPeriod or step == 1:
                            timeCount = 0
                            """ PMV ?????? """
                            self.ui.line_ta.setText(str(round(tRoomLast, 2)))
                            self.ui.line_tr.setText(str(round(tRoomLast - 1, 2)))
                            self.pmvCalc()
                            pmvRoom = PMV
                            pid = PID.PID(1.0, 0.0, 5.0)
                            if adjustNum == 0:
                                pid.SetPoint = pmvMin
                            else:
                                pid.SetPoint = 0.5 * (pmvMin + pmvMax)
                            pid.setdelta_time(controllPeriod)
                            pid.update(pmvRoom)
                            output = pid.output
                            #print(output)
                            if pmvRoom < pid.SetPoint or adjustNum == 1:
                                dQRoom = stepLength * (hWall * AreaRoom * (Walltem - tRoomLast))
                                if adjustNum == 0 or pmvRoom > pmvMax:
                                    adjustNum += 1
                            else:
                                Qaircondition = min(-Qcapacity * 2500 * minPowerRatio, Qcapacity * 2500 * max(-1.0, output))
                                dQRoom = stepLength * (hWall * AreaRoom * (Walltem - tRoomLast) + Qaircondition)

                    tRoomNew = tRoomLast + 0.001 * dQRoom / mRoom / cpRoom
                    tRoomLast = tRoomNew

                    """ ???????????? """
                    calcTime.append(step * stepLength)
                    calcTem.append(tRoomNew)
                    calcPmv.append(pmvRoom)

                    self.updateSignal.emit()
                else:
                    break
            if step == stepNum:
                self.updateSignal.emit()
                self.ui.button_stop.setText("??????")

        _thread.start_new_thread(thread_Simulation, (self,))

    def stop(self):
        global state
        if state == True:
            self.ui.button_begin.setText("??????")
            state = False
        else:
            self.ui.button_begin.setText("-")
            state = True

    def deviceChange(self):  # ??????????????????
        if self.ui.checkBox_tem.isChecked():
            self.ui.label_ta.setText("C???????????????(???)")
            self.ui.label_tr.setText("BC???????????????(???)")
            self.ui.label_hum.setText("C???????????????(%)")
        else:
            self.ui.label_ta.setText("A???????????????(???)")
            self.ui.label_tr.setText("AB???????????????(???)")
            self.ui.label_hum.setText("A???????????????(%)")
        if self.ui.checkBox_wave.isChecked():
            self.ui.label_met.setText("BD????????????(met)")
            self.ui.label_work.setText("BD???????????????(met)")
        else:
            self.ui.label_met.setText("B????????????(met)")
            self.ui.label_work.setText("B???????????????(met)")

    def valueDefault1(self):  # ???????????????????????????
        self.ui.line_roomL.setText(str(5.0))
        self.ui.line_roomW.setText(str(4.0))
        self.ui.line_roomH.setText(str(3.0))
        self.ui.line_ta.setText(str(19.0))
        self.ui.line_tr.setText(str(18.0))
        self.ui.line_hum.setText(str(40.0))
        self.ui.line_va.setText(str(0.1))
        self.ui.line_met.setText(str(1.2))
        self.ui.line_work.setText(str(0.0))

    def valueDefault2(self):  # ???????????????????????????
        self.ui.line_roomL.setText(str(5.0))
        self.ui.line_roomW.setText(str(4.0))
        self.ui.line_roomH.setText(str(3.0))
        self.ui.line_ta.setText(str(38.0))
        self.ui.line_tr.setText(str(37.0))
        self.ui.line_hum.setText(str(50.0))
        self.ui.line_va.setText(str(0.3))
        self.ui.line_met.setText(str(2))
        self.ui.line_work.setText(str(0.5))

    def valueClear(self):  # ????????????
        self.ui.line_roomL.setText("")
        self.ui.line_roomW.setText("")
        self.ui.line_roomH.setText("")
        self.ui.line_ta.setText("")
        self.ui.line_tr.setText("")
        self.ui.line_hum.setText("")
        self.ui.line_va.setText("")
        self.ui.line_met.setText("")
        self.ui.line_work.setText("")
        self.ui.label_resultPmvVal.setText("None")
        self.ui.label_resultPpdVal.setText("None")

    def pmvCalc(self):  # PMV??????
        global PMV
        clo = 1.0
        try:
            ta = float(self.ui.line_ta.text())  # ???????????? C      ?????????????????????????????????????????????
            tr = float(self.ui.line_tr.text())  # ?????????????????? C   AI?????????/??????????????????/?????????????????? ????????????
            hum = 0.01 * float(self.ui.line_hum.text())  # ???????????? -         ?????????????????????????????????????????????
            va = float(self.ui.line_va.text())  # ?????? m/s        ?????????/????????????????????? + AI?????????
            Met = float(self.ui.line_met.text())  # ????????? met      ??????????????????/AI????????? ?????????????????? -> met??????????????? -> met???
            WME = float(self.ui.line_work.text())  # ???????????? WME    AI????????? ??????????????? -> WME??????????????? met ?????????
            cloSelect = self.ui.combo_clo.currentText()  # ???????????? clo    AI????????? ??????????????? ???????????????
            clo = 0.5 if cloSelect == "?????????-??????" else (
                1.0 if cloSelect == "????????????-???" else (1.1 if cloSelect == "?????????-??????" else 1.3))
        except ValueError:
            self.ui.label_resultPmvVal.setText('<font color=\"#FFFF0000\">Error input</font>')
            self.ui.label_resultPpdVal.setText('<font color=\"#FFFF0000\">Error input</font>')
        else:
            # ??????????????????
            icl = 0.155 * clo
            pa = math.exp(16.6536 - 4030.183 / (ta + 235)) * hum * 10
            fcl = 1 + 1.29 * icl if icl < 0.078 else 1.05 + 0.645 * icl
            hc = hcf = 12.1 * math.sqrt(va)
            Ta = ta + 273
            Tr = tr + 273
            M = Met * 58.15
            W = WME * 58.15
            MW = M - W
            Tcla = Ta + (35.5 - ta) / (3.5 * icl + 0.1)
            xf = xn = Tcla / 100
            P1 = icl * fcl
            P2 = P1 * 3.96
            P3 = P1 * 100
            P4 = P1 * Ta
            P5 = 308.7 - 0.028 * MW + P2 * math.pow((Tr / 100), 4)

            # ????????????Tcl
            iteration = 1
            while iteration <= 1000:
                xf = (xf + xn) / 2
                hcn = 2.38 * math.pow(math.fabs(100 * xf - Ta), 0.25)
                hc = max(hcf, hcn)
                xn = (P5 + P4 * hc - P2 * math.pow(xf, 4)) / (100 + P3 * hc)
                if math.fabs(xf - xn) < 1e-8:
                    break
                iteration += 1
            Tcl = 100 * xn

            # ??????????????????
            HL1 = 3.05 * 0.001 * (5733 - 6.99 * MW - pa)
            HL2 = 0.42 * (MW - 58.15) if MW > 58.15 else 0
            HL3 = 1.7 * 0.00001 * M * (5867 - pa)
            HL4 = 0.0014 * M * (34 - ta)
            HL5 = 3.96 * fcl * (math.pow(xn, 4) - math.pow((Tr / 100), 4))
            HL6 = fcl * hc * (Tcl - Ta)
            ts = 0.303 * math.exp(-0.036 * M) + 0.028

            # ??????
            PMV = round(ts * (MW - HL1 - HL2 - HL3 - HL4 - HL5 - HL6), 2)
            PPD = round(100 - 95 * math.exp(-0.03353 * math.pow(PMV, 4) - 0.2179 * PMV * PMV), 2)
            if iteration <= 1000:
                self.ui.label_resultPmvVal.setText(str(PMV))
                self.ui.label_resultPpdVal.setText(str(PPD) + "%")
            else:
                self.ui.label_resultPmvVal.setText('<font color=\"#FFFF0000\">Error iteration</font>')
                self.ui.label_resultPpdVal.setText('<font color=\"#FFFF0000\">Error iteration</font>')

    def weatherUrl1(self):
        self.ui.line_url.setText("http://www.weather.com.cn/data/sk/")
        self.ui.line_ip.setText("47.242.59.65")
        self.ui.line_port.setText("8123")

    def weatherUrl2(self):
        self.ui.line_url.setText("http://wthrcdn.etouch.cn/weather_mini?city=")
        self.ui.line_ip.setText("47.242.59.65")
        self.ui.line_port.setText("8123")

    def weatherGet(self):
        citySelect = self.ui.combo_air.currentText()
        url = self.ui.line_url.text()
        if url == "http://www.weather.com.cn/data/sk/":
            url += "101010100.html" if citySelect == "??????" else ("101020100.html" if citySelect == "??????" else (
                "101280101.html" if citySelect == "??????" else ("101280601.html" if citySelect == "??????" else (
                    "101110101.html" if citySelect == "??????" else "101110200.html"))))
            try:
                resText = str(requests.get(url).content, 'utf-8')
            except requests.exceptions.ConnectionError:
                print("error")
            else:
                currentTem = str(re.findall(r"temp\":\"(.+?)\"", resText)).strip("['']") + "???"
                airPower = str(re.findall(r"WS\":\"(.+?)\"", resText)).strip("['']")
                airHum = str(re.findall(r"SD\":\"(.+?)\"", resText)).strip("['']")
                self.ui.label_state.setText('<font color=\"#007500\">Respond</font>')
                self.ui.label_line1.setText("")
                self.ui.label_airGeneral.setText(citySelect)
                self.ui.label_airTemMin.setText(currentTem)
                self.ui.label_airTemMax.setText(airHum)
                self.ui.label_airPower.setText(airPower)
        elif url == "http://wthrcdn.etouch.cn/weather_mini?city=":
            url = url + citySelect
            res = requests.get(url)
            today = datetime.datetime.now().strftime('%d') + "???"
            tomorrow = str(int(datetime.datetime.now().strftime('%d')) + 1) + "???"
            weather = re.findall(r"%s(.+?)%s" % (today, tomorrow), res.text)
            hotTem = "???" + str(re.findall(r"?????? (.+?)\"", str(weather))).strip("['']")
            coldTem = "???" + str(re.findall(r"?????? (.+?)\"", str(weather))).strip("['']")
            airPower = str(re.findall(r"CDATA\[(.+?)\]", str(weather))).strip("['']") + "???"
            general = str(re.findall(r"type\":\"(.+?)\"", str(weather))).strip("['']")
            self.ui.label_state.setText('<font color=\"#007500\">Respond</font>')
            self.ui.label_line1.setText("-")
            self.ui.label_airGeneral.setText(general)
            self.ui.label_airTemMin.setText(coldTem)
            self.ui.label_airTemMax.setText(hotTem)
            self.ui.label_airPower.setText(airPower)
        else:
            self.ui.label_state.setText('<font color=\"#FFFF0000\">Url Error</font>')
            self.ui.label_stateInfo.setText('<font color=\"#FFFF0000\">Please input correct url</font>')
            self.ui.label_airGeneral.setText("??????")
            self.ui.label_airTemMin.setText("??????")
            self.ui.label_line1.setText("")
            self.ui.label_airTemMax.setText("???%")
            self.ui.label_airPower.setText("?????????")

        pmvGetSelect = self.ui.combo_fitPmv.currentText()
        if pmvGetSelect == "????????????":
            HOST = self.ui.line_ip.text()
            PORT = int(self.ui.line_port.text())
            try:
                BUFSIZ = 1024
                ADDR = (HOST, PORT)
                tcpCliSock = socket(AF_INET, SOCK_STREAM)
                tcpCliSock.connect(ADDR)
                data = "get_PMV_interval"
                tcpCliSock.send(data.encode())
                respond = tcpCliSock.recv(BUFSIZ)
                tcpCliSock.close()
            except (ConnectionRefusedError):
                self.ui.label_stateInfo.setText('<font color=\"#FFFF0000\">Connection failed</font>')
                self.ui.label_state.setText('<font color=\"#FFFF0000\">Port Err</font>')
                self.ui.line_pmvMin.setText("")
                self.ui.line_pmvMax.setText("")
            else:
                self.ui.label_stateInfo.setText('<font color=\"#007500\">%s</font>' % (respond.decode('utf-8')))
                pmvlist = respond.decode('utf-8')[-8:].split(" ")
                self.ui.line_pmvMin.setText(pmvlist[0])
                self.ui.line_pmvMax.setText(pmvlist[2])
        else:
            self.ui.line_pmvMin.setText("")
            self.ui.line_pmvMax.setText("")
            self.ui.label_state.setText("Status")
            self.ui.label_stateInfo.setText("Input by user")

    def weatherClear(self):
        self.ui.line_url.setText("")
        self.ui.label_airGeneral.setText("")
        self.ui.label_airGeneral.setText("??????")
        self.ui.label_airTemMin.setText("??????")
        self.ui.label_line1.setText("")
        self.ui.label_airTemMax.setText("???%")
        self.ui.label_airPower.setText("?????????")
        self.ui.line_ip.setText("")
        self.ui.line_port.setText("")
        self.ui.label_state.setText("Status")
        self.ui.label_stateInfo.setText("Waiting for input")
        self.ui.line_pmvMin.setText("")
        self.ui.line_pmvMax.setText("")


app = QApplication([])
app.setWindowIcon(QIcon('logo.png'))
stats = Stats()

stats.ui.show()
app.exec_()
