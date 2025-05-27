"""
Author: YuLin Chen; Shiyue Wang
Auto_test.py
包含源表、信号发生器

"""


import sys
import time
import pandas as pd
import pyvisa as visa

from PyQt5.QtWidgets import QMainWindow,QApplication,QDialog,QTableWidget, QTableWidgetItem, QScrollArea
from pyvisa.events import event
from qt_material import apply_stylesheet


from Auto_test_UI import Ui_Dialog  # 主界面

from saveload import Ui_Dialog_saveload  # 保存加载界面
from save import Ui_Dialog_save  # 保存加载的保存界面
from load import Ui_Dialog_load  # 保存加载的确认界面
from delt import Ui_Dialog_del  # 保存加载的删除界面
from datetime import datetime  # 获取当前时间

from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QVBoxLayout

from Generator_control import AFG3102C  # AFG3102C控制函数
from Generator_control import AFG31102  # AFG31102控制函数
from Control_Keithley2410 import keithley2410   # 2410控制函数
from Control_Keithley2430 import keithley2430   # 2430控制函数
from Plot_Keithley2410 import voltagePlotWidget, currentPlotWidget, PulsePreviewWidget, SweepWidget
from Plot_Keithley2430 import voltagePlotWidget2430, currentPlotWidget2430, PulsePreviewWidget2430, SweepWidget2430, PulseResultWidget2430

from saveload_f import Dialog_saveload
from about_f import Dialog_about

########################################################################电压源模式线程######################################################################
class VoltageThread(QThread):       # 电压源模式线程 在set_target_voltage()函数中调用线程
    finished = pyqtSignal()     # 完成信号
    error = pyqtSignal(str)     # 错误信号

    def __init__(self, keithley, target_vol, speed=5):
        super().__init__()
        self.keithley = keithley        # 仪器控制对象
        self.target_vol = target_vol    # 目标电压值
        self.speed = speed              # 电压变化速度（未直接使用）

    def run(self):
        if not self.keithley.kei2410.query(":OUTPUT?").strip() == '1':
            self.keithley.outputOn()    # 确保输出开启
        try:
            self.keithley.directSetVoltageOutput(self.target_vol)       # 直接设置电压
            self.finished.emit()        # 发射完成信号
        except Exception as e:
            self.error.emit(str(e))     # 发射错误信息

class Voltage2430Thread(QThread):  # 电压源模式线程 在set_target_voltage()函数中调用线程
    finished = pyqtSignal()  # 完成信号
    error = pyqtSignal(str)  # 错误信号

    def __init__(self, keithley, target_vol):
        super().__init__()
        self.keithley2430 = keithley  # 仪器控制对象
        self.target_vol = target_vol  # 目标电压值

    def run(self):
        if not self.keithley2430.kei2430.query(":OUTPUT?").strip() == '1':
            self.keithley2430.outputOn()  # 确保输出开启
        try:
            self.keithley2430.directSetVoltageOutput(self.target_vol)  # 直接设置电压
            self.finished.emit()  # 发射完成信号
        except Exception as e:
            self.error.emit(str(e))
#######################################################################电流源模式线程#############################################################################
class CurrentThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, keithley, target_curr, speed=5):
        super().__init__()
        self.keithley = keithley
        self.target_curr = target_curr
        self.speed = speed

    def run(self):
        if not self.keithley.get_output_state():
            self.keithley.outputOn()
        try:
            self.keithley.directSetCurrentOutput(self.target_curr)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class Current2430Thread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, keithley, target_curr):
        super().__init__()
        self.keithley2430 = keithley
        self.target_curr = target_curr

    def run(self):
        if not self.keithley2430.get_output_state():
            self.keithley2430.outputOn()
        try:
            self.keithley2430.directSetCurrentOutput(self.target_curr)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

#######################################################################扫描模式线程#############################################################################
class ScanningThread(QThread):
    data_ready = pyqtSignal(dict)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, keithley, config, source_mode):
        super().__init__()
        self.keithley = keithley
        self.config = config
        self.source_mode = source_mode  # 0-电流源 1-电压源
        self.running = True
        self.sweep_done = False

    def run(self):
        try:
            # 配置仪器
            if self.source_mode == 0:
                self.keithley.CurrentSweep(
                    sweep_type=self.config['sweep_type'],
                    start=self.config['start'],
                    stop=self.config['stop'],
                    step=self.config['step'],
                    point=self.config['points'],
                    compliance=self.config['protection'],
                    delay=self.config['delay']
                )
                self.keithley.saveCurrentSweepData()  ############
                self.running = False
            else:
                self.keithley.VoltageSweep(
                    sweep_type=self.config['sweep_type'],
                    start=self.config['start'],
                    stop=self.config['stop'],
                    step=self.config['step'],
                    point=self.config['points'],
                    compliance=self.config['protection'],
                    delay=self.config['delay']
                )
                self.keithley.saveVoltageSweepData()      ############3
                self.running = False

            # 等待扫描完成或超时
            timeout = 60  # 1分钟超时（秒）
            start_time = time.time()
            while self.running and not self.keithley.sweep_done:
                if time.time() - start_time > timeout:
                    raise TimeoutError("扫描操作超时")
                time.sleep(0.1)

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

        finally:
            # 必要的清理操作，如关闭输出
            self.running = False
            self.keithley.outputOff()

    def stop(self):
        self.running = False


class Scanning2430Thread(QThread):
    data_ready = pyqtSignal(dict)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, keithley, config, source_mode):
        super().__init__()
        self.keithley2430 = keithley
        self.config = config
        self.source_mode = source_mode  # 0-电流源 1-电压源
        self.running = True
        self.sweep_done = False

    def run(self):
        try:
            # 配置仪器
            if self.source_mode == 0:
                self.keithley2430.CurrentSweep(
                    sweep_type=self.config['sweep_type'],
                    start=self.config['start'],
                    stop=self.config['stop'],
                    step=self.config['step'],
                    point=self.config['points'],
                    compliance=self.config['protection'],
                    delay=self.config['delay']
                )
                self.keithley2430.saveCurrentSweepData()  ############
                self.running = False
            else:
                self.keithley2430.VoltageSweep(
                    sweep_type=self.config['sweep_type'],
                    start=self.config['start'],
                    stop=self.config['stop'],
                    step=self.config['step'],
                    point=self.config['points'],
                    compliance=self.config['protection'],
                    delay=self.config['delay']
                )
                self.keithley2430.saveVoltageSweepData()      ############3
                self.running = False

            # 等待扫描完成或超时
            timeout = 60  # 1分钟超时（秒）
            start_time = time.time()
            while self.running and not self.keithley2430.sweep_done:
                if time.time() - start_time > timeout:
                    raise TimeoutError("扫描操作超时")
                time.sleep(0.1)

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

        finally:
            # 必要的清理操作，如关闭输出
            self.running = False
            self.keithley2430.outputOff()

    def stop(self):
        self.running = False

####################################################################### 定时器主线程相关函数 #############################################################################

class Keithley2430MainThread(QThread):
    data_updated = pyqtSignal(float, float)  # 电压, 电流
    error_occurred = pyqtSignal(str)

    def __init__(self, keithley2430):
        super().__init__()
        self.keithley2430 = keithley2430
        self.running = True

    def run(self):
        while self.running:
            try:
                if self.keithley2430 is None:
                    raise ValueError("Keithley2430实例不存在")
                if self.keithley2430.get_output_state():
                    voltage = self.keithley2430.showVoltage()
                    current = self.keithley2430.showCurrent()
                    self.data_updated.emit(voltage, current)
                else:
                    self.data_updated.emit(0.0, 0.0)
                self.msleep(1000)  # 1秒间隔
            except Exception as e:
                self.error_occurred.emit(str(e))
                break

    def stop(self):
        self.running = False

####################################################################### MyDialog类 #############################################################################
class MyDialog(QMainWindow, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)      # 初始化UI
        self.w_confirmInstrumentsSources.clicked.connect(self.instrumentsConnect)
        self.w_checkUsableInstrumentsSources.clicked.connect(self.checkUsableInstrumentsSources)
        self.pushButton_saveload.clicked.connect(self.show_saveload_dialog)
        self.pushButton_about.clicked.connect(self.show_about_dialog)

    #######################################################仪器初始化连接相关函数#####################################################
    def checkUsableInstrumentsSources(self):
        rm = visa.ResourceManager()
        InstrumentsResources = rm.list_resources()
        print(InstrumentsResources)
        # 将元组转换为字符串显示在textedit中
        self.w_usableSources.setPlainText(str(InstrumentsResources))
        # 清空下拉框现有选项
        self.w_2430COMchoice.clear()
        self.w_2430COMchoice.addItem("None")
        self.w_2410COMchoice.clear()
        self.w_2410COMchoice.addItem("None")
        self.w_GeneratorCOMchoice.clear()
        self.w_GeneratorCOMchoice.addItem("None")
        # 遍历资源并添加到下拉框
        for resource in InstrumentsResources:
            # 添加每个资源到下拉框
            self.w_2430COMchoice.addItem(resource)
            self.w_2410COMchoice.addItem(resource)
            self.w_GeneratorCOMchoice.addItem(resource)


    def instrumentsConnect(self):
        self.current_data = None
        self.current_data2430 = None

        address2430 = self.w_2430COMchoice.currentText()
        address2410 = self.w_2410COMchoice.currentText()
        address_Generator = self.w_GeneratorCOMchoice.currentText()
        # address_Oscilloscope = self.w_OscilloscopeCOMchoice.currentText()
        print(address2430, address2410, address_Generator)

        try:
            # 初始化2410连接配置
            self.keithley = keithley2410(str(address2410))
            self.keithley.testIO()
            self.keithley.safe_initialize()
        except Exception as e:
            QMessageBox.critical(self, "2410连接错误", f"无法连接2410: {str(e)}")
            self.keithley = None  # 确保属性存在

        try:
            # 初始化2430连接配置
            self.keithley2430 = keithley2430(str(address2430))
            self.keithley2430.testIO()
            self.keithley2430.safe_initialize()
        except Exception as e:
            QMessageBox.critical(self, "2430连接错误", f"无法连接2430: {str(e)}")
            self.keithley2430 = None  # 确保属性存在

        try:
            # 初始化信号发生器连接配置
            self.AFG1 = AFG31102(str(address_Generator))
            self.AFG1.testIO()
        except Exception as e:
            QMessageBox.critical(self, "信号发生器连接错误", f"无法连接信号发生器: {str(e)}")
            self.AFG1 = None  # 确保属性存在

        # try:
        #     # 初始化示波器连接配置
        #     self.Oscilloscope = MDO44(str(address_Oscilloscope))
        #     self.Oscilloscope.testIO()
        # except Exception as e:
        #     QMessageBox.critical(self, "示波器连接错误", f"无法连接示波器: {str(e)}")
        #     self.Oscilloscope = None  # 确保属性存在

        # 仅当仪器成功连接时初始化相关组件
        if self.keithley2430 is not None:
            self.init_2430voltage_mode()
            self.init2430_current_mode()
            self.init2430_pulse_mode()
            self.init2430_scanning_mode()
            # self.timer2430MainThread()      # 初始化2430主线程定时器

        if self.keithley is not None:
            self.init_current_mode()
            self.init_voltage_mode()
            self.init_pulse_mode()
            self.init_scanning_mode()
            # self.timerMainThread()          # 初始化主线程定时器

        if self.AFG1 is not None:
            self.Generator_UI_init()

        self.check_output_state()   # 初始化当前输出状态

        # 连接成功后初始化定时器
        if self.keithley is not None:
            # 获取当前选中的tab索引（0表示电压源模式）
            current_tab = self.tabWidget.currentIndex()
            # 手动触发tab切换事件
            self.on_tab_changed(current_tab)

        if self.keithley2430 is not None:
            # 获取2430当前选中的tab索引（0表示电压源模式）
            current_2430tab = self.kei2430tabWidget.currentIndex()
            # 手动触发2430的tab切换事件
            self.on_2430tab_changed(current_2430tab)

        self.tabWidget.currentChanged.connect(self.on_tab_changed)
        self.kei2430tabWidget.currentChanged.connect(self.on_2430tab_changed)


    ################################################################## 模式切换相关函数 ################################################################
    def on_tab_changed(self, index):        # 2410处理标签页切换时的仪器重置
        try:
            if self.keithley is None:
                return
            # 停止当前可能存在的线程和定时器
            if hasattr(self, 'voltage_thread') and self.voltage_thread.isRunning():
                self.voltage_thread.quit()
            if hasattr(self, 'current_thread') and self.current_thread.isRunning():
                self.current_thread.quit()
            if hasattr(self, 'timer') and self.timer.isActive():
                self.timer.stop()

            # 关闭仪器输出
            self.keithley.outputOff()
            self.keithley.resetInstruments()

            # 根据标签页设置源模式并重置参数
            if index == 0:  # 电压源模式
                self.keithley.setSourceVoltage()
                self.keithley.directSetVoltageOutput(0)  # 重置电压输出为0
            elif index == 1:  # 电流源模式
                self.keithley.setSourceCurrent()
                self.keithley.directSetCurrentOutput(0)  # 重置电流输出为0
            elif index == 2:  # 脉冲模式
                pass  # 根据需求添加脉冲模式重置
            elif index == 3:  # 扫描模式
                self.keithley.setSourceCurrent()
                self.keithley.directSetCurrentOutput(0)  # 重置电流输出为0

            # 更新UI状态
            self.check_output_state()
            # 重启定时器
            # 仅在非扫描模式时启动定时器
            if index != 3 and hasattr(self, 'timer'):
                self.timer.start(1000)
            # if index != 3:
            #     self.timer.start(1000)

        except Exception as e:
            QMessageBox.critical(self, "模式切换错误", f"切换时发生错误: {str(e)}")
        # finally:
        #     # 仅在非扫描模式时启动定时器
        #     if index != 3:
        #         self.timer.start(1000)

    def on_2430tab_changed(self, index):        # 处理2430标签页切换事件
        try:
            if self.keithley2430 is None:
                return

            # 停止可能存在的2430监控输出线程和定时器
            if hasattr(self, 'keithley2430_thread') and self.keithley2430_thread.isRunning():
                self.keithley2430_thread.stop()
                self.keithley2430_thread.quit()
                self.keithley2430_thread.wait(500)

            # 关闭输出并重置仪器
            self.keithley2430.outputOff()
            self.keithley2430.resetInstruments()

            # 根据标签页设置源模式
            if index == 0:  # 电压源模式
                self.keithley2430.setSourceVoltage()
                # 重置输出电压为0
                self.keithley2430.directSetVoltageOutput(0)
                self.timer2430MainThread()
            elif index == 1:  # 电流源模式
                self.keithley2430.setSourceCurrent()
                # 重置输出电流为0
                self.keithley2430.directSetCurrentOutput(0)
                self.timer2430MainThread()
            elif index == 2:  # 脉冲模式
                self.keithley2430.setSourceCurrent()    # 默认设置为电流源输出
                self.keithley2430.directSetCurrentOutput(0) # 重置输出电流为0
            elif index == 3:
                self.keithley2430.setSourceCurrent()
                self.keithley2430.directSetCurrentOutput(0)
            # 更新UI输出状态显示
            self.check2430_output_state()
            # 重启2430监控线程
            # self.timer2430MainThread()
            # 确保定时器重新启动
            if hasattr(self, 'keithley2430_thread'):
                self.keithley2430_thread.start()


        except Exception as e:
            QMessageBox.critical(self, "模式切换错误", f"2430切换时发生错误: {str(e)}")
        finally:
            # 确保定时器重新启动
            if hasattr(self, 'keithley2430_thread'):
                self.keithley2430_thread.start()



    #######################################################################定时器主线程相关函数#############################################################################

    def timerMainThread(self):
        # self.timer = QTimer(self)
        # self.timer.timeout.connect(self.on_timeout)  # 定时根据当前模式决定主线程
        # self.timer.start(1000)  # 每秒轮询仪器状态
        # 确保仪器已连接
        if self.keithley is None:
            return
        # 停止旧定时器（如果存在）
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
            del self.timer
        # 创建新定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timeout)
        self.timer.start(1000)

    def on_timeout(self):   # 定时器回调，根据当前标签页更新对应模式
        try:
            output_on = self.keithley.get_output_state()  # 查询输出状态
            current_tab = self.tabWidget.currentIndex()     # 查询当前标签页
            # 更新当前标签页对应的输出状态
            if current_tab == 0:  # 电压源模式
                self.update_measurements()
            elif current_tab == 1:  # 电流源模式
                self.update_current_measurements()
            self.check_output_state()
        except Exception as e:
            print(f"状态更新错误: {str(e)}")
            # # 可選：尝试重新初始化定时器
            # self.timerMainThread()

    def timer2430MainThread(self):
            if self.keithley2430 is None:
                return  # 无连接时不启动线程
            self.keithley2430_thread = Keithley2430MainThread(self.keithley2430)
            self.keithley2430_thread.data_updated.connect(self.update2430_ui)
            self.keithley2430_thread.error_occurred.connect(self.handle2430_error)
            self.keithley2430_thread.start()

    def update2430_ui(self, voltage, current):
        # 更新2430的UI显示
        self.w_2430SourceVcurrentDisplay.setText(f"{current:.4e}")
        self.w_2430SourceVResDisplay.setText(f"{voltage / current:.2f}" if current != 0 else "N/A")

    def handle2430_error(self, error_msg):
        QMessageBox.critical(self, "2430错误", error_msg)
        self.keithley2430_thread.stop()  # 停止问题线程

    #######################################################电压源模式相关函数#####################################################

    def init_voltage_mode(self):        # 初始化电压源绘图组件
        # 初始化绘图部件 将widget区域替换为电压源绘图组件
        self.plot_widget = voltagePlotWidget()
        layout = QVBoxLayout(self.voltagePlot)
        layout.addWidget(self.plot_widget)
        # 设置保护电流输入框为单行模式
        self.w_protectionCurrentInput.setMaximumHeight(30)
        self.w_protectionCurrentInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_protectionCurrentInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_protectionCurrentInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        # 设置输出电压输入框为单行模式
        self.w_outputVoltageInput.setMaximumHeight(30)
        self.w_outputVoltageInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_outputVoltageInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_outputVoltageInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        # 调整文本输入框字体大小和边距
        self.w_protectionCurrentInput.setStyleSheet("""
                    QTextEdit {
                        padding: 0px;     /* 减少内边距 */
                        margin: 0px;      /* 减少外边距 */
                    }
                """)
        self.w_outputVoltageInput.setStyleSheet("""
                    QTextEdit {
                        padding: 0px;
                        margin: 0px;
                    }
                """)
        # 设置复选框样式
        self.w_checkBox.setStyleSheet("""
                            QCheckBox {
                                color: #39c5bb;
                            }
                        """)

        # 设置电压源模式默认保护电流值105uA 设置默认输出电压为0
        self.w_protectionCurrentInput.setPlainText("105")  # 数值设为105
        self.w_comboBox.setCurrentIndex(2)  # 单位选择μA（对应索引2）
        self.w_outputVoltageInput.setPlainText("0")
        self.w_comboBox_2.setCurrentIndex(0)  # 默认选择V

        # 连接电压源信号
        self.w_save2table.clicked.connect(self.save_data)
        self.w_checkBox.stateChanged.connect(self.toggle_output)
        self.w_stopmeasure.clicked.connect(self.pause_measurement)
        self.w_stopmeasure_2.clicked.connect(self.resume_measurement)
        self.w_confirmSVsettings.clicked.connect(self.set_protection_current)
        self.w_confirmSVsettings.clicked.connect(self.set_target_voltage)


    def check_output_state(self):       # 检查并更新当前标签页的输出状况的复选框
        try:
            output_on = self.keithley.get_output_state()
            current_tab = self.tabWidget.currentIndex()
            if current_tab == 0:    # 电压源模式
                with QtCore.QSignalBlocker(self.w_checkBox):  # 使用上下文管理器阻止信号
                    self.w_checkBox.setChecked(Qt.Checked if output_on else Qt.Unchecked)
                    self.w_checkBox.setText("输出开启" if output_on else "输出关闭")
            elif current_tab == 1:   # 电流源模式
                with QtCore.QSignalBlocker(self.w_OutputCheck):  # 使用上下文管理器阻止信号
                    self.w_OutputCheck.setChecked(Qt.Checked if output_on else Qt.Unchecked)
                    self.w_OutputCheck.setText("输出开启" if output_on else "输出关闭")
        except Exception as e:
            print(f"状态检查错误: {str(e)}")

    def update_output_state(self, state):
        actual_state = self.keithley.kei2410.query(":OUTPUT?").strip()
        if (state == Qt.Checked and actual_state != '1') or \
                (state != Qt.Checked and actual_state == '1'):
            self.w_checkBox.setChecked(not state)

    def set_protection_current(self):
        text_value = self.w_protectionCurrentInput.toPlainText()
        value = float(text_value)
        unit = self.w_comboBox.currentText()
        # 单位转换
        multiplier = {
            'm': 1e-3,
            'u': 1e-6,
            'n': 1e-9
        }.get(unit, 1)

        try:
            self.keithley.setCurrentProtection(value * multiplier)
            QMessageBox.information(self, "成功", "保护电流设置成功!")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def set_target_voltage(self):
        try:
            # 获取输入值和单位
            text_value = self.w_outputVoltageInput.toPlainText()
            value = float(text_value)
            unit = self.w_comboBox_2.currentText()

            # 单位转换为伏特(V)
            multiplier = {
                'm': 1e-3,  # 毫伏 -> 伏特
                'u': 1e-6,  # 微伏 -> 伏特
                'n': 1e-9  # 纳伏 -> 伏特
            }.get(unit, 1)  # 默认为伏特，无需转换

            target_vol = value * multiplier

            # 输入有效性验证
            if abs(target_vol) > 1100:
                raise ValueError("电压值超出安全范围 (最大 ±1100V)")

            # 启动电压设置线程
            self.voltage_thread = VoltageThread(
                self.keithley, target_vol, speed=5
            )
            self.voltage_thread.finished.connect(lambda: (
                QMessageBox.information(self, "完成", "电压设置完成!"),
                self.plot_widget.loadData(),
                self.update_measurements()
            ))
            self.voltage_thread.error.connect(
                lambda e: QMessageBox.critical(self, "错误", e)
            )
            self.voltage_thread.start()

        except ValueError as ve:
            QMessageBox.critical(self, "输入错误", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生未知错误: {str(e)}")

    def toggle_output(self, state):
        try:
            if state == Qt.Checked:
                self.keithley.outputOn()
                # self.w_checkBox.setText("输出开启")
            else:
                self.keithley.outputOff()
                # self.w_checkBox.setText("输出关闭")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
            self.w_checkBox.setChecked(not state)
        finally:
            # 立即更新一次状态显示
            self.check_output_state()

    def update_measurements(self):
        try:
            output_on = self.keithley.get_output_state()
            if not output_on:
                self.w_currentDisplay.setText("N/A")
                self.w_resDisplay.setText("N/A")
                self.current_data = None
                return

            # 读取当前测量值
            current = self.keithley.showCurrent()
            voltage = self.keithley.showVoltage()
            resistance = 0

            # 更新界面显示
            self.w_currentDisplay.setText(f"{current:.4e}")
            self.w_resDisplay.setText(f"{resistance:.2f}")

            # 存储当前数据，不自动添加到DataFrame
            self.current_data = {
                "Timestamp": pd.Timestamp.now(),
                "Voltage(V)": voltage,
                "Current(A)": current,
                "Resistor(Ohm)": resistance,
                "备注": ""
            }


        except Exception as e:
            print(f"测量更新错误: {str(e)}")

    def save_data(self):
        # self.plot_widget.sync_table_data()  # 确保保存前同步表格数据
        if self.current_data is None:
            QMessageBox.warning(self, "警告", "无可用数据!")
            return
        # 添加当前数据到DataFrame
        self.plot_widget.df = pd.concat(
            [self.plot_widget.df, pd.DataFrame([self.current_data])],
            ignore_index=True
        )
        # 同步表格数据并保存
        self.plot_widget.sync_table_data()
        try:
            self.plot_widget.save_to_excel()
            QMessageBox.information(self, "成功", "数据保存成功!")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
        # 更新图表和表格显示
        self.plot_widget.updatePlot()
        self.plot_widget.updateView()

    def pause_measurement(self):
        self.timer.stop()
        try:
            self.keithley.outputOff()
        except Exception as e:
            print(f"关闭输出失败: {str(e)}")
        finally:
            self.check_output_state()  # 确保无论是否异常都更新状态

    def resume_measurement(self):
        # self.timer.start()
        # self.keithley.outputOn()
        try:
            self.keithley.outputOn()
        except Exception as e:
            print(f"开启输出失败: {str(e)}")
        finally:
            self.timer.start()
            self.check_output_state()  # 立即更新状态

    #######################################################2430电压源模式相关函数#####################################################

    def init_2430voltage_mode(self):        # 初始化电压源绘图组件
        # 初始化绘图部件 将widget区域替换为电压源绘图组件
        self.kei2430_sourceV_plot_widget = voltagePlotWidget2430()
        layout = QVBoxLayout(self.voltagePlot_2430)
        layout.addWidget(self.kei2430_sourceV_plot_widget)
        # 设置保护电流输入框为单行模式
        self.w_2430protectionCurrentInput.setMaximumHeight(30)
        self.w_2430protectionCurrentInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430protectionCurrentInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430protectionCurrentInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        # 设置输出电压输入框为单行模式
        self.w_2430outputVoltageInput.setMaximumHeight(30)
        self.w_2430outputVoltageInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430outputVoltageInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430outputVoltageInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        # 调整文本输入框字体大小和边距
        self.w_2430protectionCurrentInput.setStyleSheet("""
                    QTextEdit {
                        padding: 0px;     /* 减少内边距 */
                        margin: 0px;      /* 减少外边距 */
                    }
                """)
        self.w_2430outputVoltageInput.setStyleSheet("""
                    QTextEdit {
                        padding: 0px;
                        margin: 0px;
                    }
                """)
        # 设置复选框样式
        self.w_2430SourceVOutputCheck.setStyleSheet("""
                            QCheckBox {
                                color: #39c5bb;
                            }
                        """)
        # 连接电压源信号
        self.w_2430_sourceV_save2table.clicked.connect(self.save2430_data)
        self.w_2430SourceVOutputCheck.stateChanged.connect(self.toggle2430_output)
        self.w_2430sourceVOutputOff.clicked.connect(self.pause2430_measurement)
        self.w_2430SourceVOutputOn.clicked.connect(self.resume2430_measurement)
        self.w_2430confirmSVsettings.clicked.connect(self.set2430_protection_current)
        self.w_2430confirmSVsettings.clicked.connect(self.set2430_target_voltage)

        self.check2430_output_state()
        # self.timer2430MainThread()      # 开启主线程


    def check2430_output_state(self):       # 检查并更新当前标签页的输出状况的复选框
        try:
            output_on = self.keithley2430.get_output_state()
            current_tab = self.kei2430tabWidget.currentIndex()
            if current_tab == 0:    # 电压源模式
                with QtCore.QSignalBlocker(self.w_2430SourceVOutputCheck):  # 使用上下文管理器阻止信号
                    self.w_2430SourceVOutputCheck.setChecked(Qt.Checked if output_on else Qt.Unchecked)
                    self.w_2430SourceVOutputCheck.setText("输出开启" if output_on else "输出关闭")
            elif current_tab == 1:   # 电流源模式
                with QtCore.QSignalBlocker(self.w_2430SourceIOutputCheck):  # 使用上下文管理器阻止信号
                    self.w_2430SourceIOutputCheck.setChecked(Qt.Checked if output_on else Qt.Unchecked)
                    self.w_2430SourceIOutputCheck.setText("输出开启" if output_on else "输出关闭")
        except Exception as e:
            print(f"状态检查错误: {str(e)}")

    def set2430_protection_current(self):
        text_value = self.w_2430protectionCurrentInput.toPlainText()
        value = float(text_value)
        unit = self.w_2430SourceVprotectionCurrentSize.currentText()
        # 单位转换
        multiplier = {
            'm': 1e-3,
            'u': 1e-6,
            'n': 1e-9
        }.get(unit, 1)
        try:
            self.keithley2430.setCurrentProtection(value * multiplier)
            QMessageBox.information(self, "成功", "保护电流设置成功!")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def set2430_target_voltage(self):
        try:
            # 获取输入值和单位
            text_value = self.w_2430outputVoltageInput.toPlainText()
            value = float(text_value)
            unit = self.w_2430_outputVoltageSize.currentText()
            # 单位转换为伏特(V)
            multiplier = {
                'm': 1e-3,  # 毫伏 -> 伏特
                'u': 1e-6,  # 微伏 -> 伏特
                'n': 1e-9  # 纳伏 -> 伏特
            }.get(unit, 1)  # 默认为伏特，无需转换
            target_vol = value * multiplier
            # 输入有效性验证
            if abs(target_vol) > 1100:
                raise ValueError("2430电压值超出安全范围 (最大 ±1100V)")

            # 启动电压设置线程
            self.voltage_thread2430 = Voltage2430Thread(
                self.keithley2430, target_vol
            )
            self.voltage_thread2430.finished.connect(lambda: (
                QMessageBox.information(self, "完成", "2430电压设置完成!"),
                self.kei2430_sourceV_plot_widget.loadData(),
                self.update2430_measurements(),
                self.check2430_output_state()
            ))
            self.voltage_thread2430.error.connect(
                lambda e: QMessageBox.critical(self, "错误", e)
            )
            self.voltage_thread2430.start()
            self.check2430_output_state()

        except ValueError as ve:
            QMessageBox.critical(self, "输入错误", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生未知错误: {str(e)}")

    def toggle2430_output(self, state):
        try:
            if state == Qt.Checked:
                self.keithley2430.outputOn()
            else:
                self.keithley2430.outputOff()
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
            self.w_checkBox.w_2430SourceVOutputCheck(not state)
        finally:
            # 立即更新一次状态显示
            self.check2430_output_state()
    def update2430_measurements(self):
        try:
            output_on = self.keithley2430.get_output_state()
            if not output_on:
                self.w_2430SourceVcurrentDisplay.setText("N/A")
                self.w_2430SourceVResDisplay.setText("N/A")
                self.current_data2430 = None
                return

            # 读取当前测量值
            current = self.keithley2430.showCurrent()
            voltage = self.keithley2430.showVoltage()
            resistance = 0

            # 更新界面显示
            self.w_2430SourceVcurrentDisplay.setText(f"{current:.4e}")
            self.w_2430SourceVResDisplay.setText(f"{resistance:.2f}")

            # 存储当前数据，不自动添加到DataFrame
            self.current_data2430 = {
                "Timestamp": pd.Timestamp.now(),
                "Voltage(V)": voltage,
                "Current(A)": current,
                "Resistor(Ohm)": resistance,
                "备注": ""
            }


        except Exception as e:
            print(f"测量更新错误: {str(e)}")

    def save2430_data(self):
        if self.current_data2430 is None:
            QMessageBox.warning(self, "警告", "无可用数据!")
            return
        # 添加当前数据到DataFrame
        self.kei2430_sourceV_plot_widget.df = pd.concat(
            [self.kei2430_sourceV_plot_widget.df, pd.DataFrame([self.current_data2430])],
            ignore_index=True
        )
        # 同步表格数据并保存
        self.kei2430_sourceV_plot_widget.sync_table_data()
        try:
            self.kei2430_sourceV_plot_widget.save_to_excel()
            QMessageBox.information(self, "成功", "数据保存成功!")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
        # 更新图表和表格显示
        self.kei2430_sourceV_plot_widget.updatePlot()
        self.kei2430_sourceV_plot_widget.updateView()

    def pause2430_measurement(self):
        if hasattr(self, 'keithley2430_thread') and self.keithley2430_thread.isRunning():
            self.keithley2430_thread.stop()  # 设置运行标志为False
            self.keithley2430_thread.quit()  # 退出线程的事件循环
            self.keithley2430_thread.wait()  # 等待线程完全退出
        try:
            self.keithley2430.outputOff()
        except Exception as e:
            print(f"关闭输出失败: {str(e)}")
        finally:
            self.check2430_output_state()  # 确保无论是否异常都更新状态

    def resume2430_measurement(self):
        try:
            # 停止现有线程（如果存在且运行中）
            if hasattr(self, 'keithley2430_thread'):
                if self.keithley2430_thread.isRunning():
                    self.keithley2430_thread.stop()
                    self.keithley2430_thread.quit()
                    self.keithley2430_thread.wait(500)  # 等待500ms确保退出

            # 创建新的线程实例
            self.keithley2430_thread = Keithley2430MainThread(self.keithley2430)
            self.keithley2430_thread.data_updated.connect(self.update2430_ui)
            self.keithley2430_thread.error_occurred.connect(self.handle2430_error)
            self.keithley2430_thread.start()  # 启动新线程

            # 开启仪器输出
            self.keithley2430.outputOn()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动失败: {str(e)}")
        finally:
            self.check2430_output_state()  # 更新UI状态

#######################################################电流源模式相关函数#####################################################

    # 初始化电流源模式绘图组件、连接信号
    def init_current_mode(self):
        # 电流源绘图部件
        self.current_plot_widget = currentPlotWidget()
        layout_current = QVBoxLayout(self.currentPlot)
        layout_current.addWidget(self.current_plot_widget)
        # 设置保护电压输入框为单行模式
        self.w_protectionVoltageInput.setMaximumHeight(30)
        self.w_protectionVoltageInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_protectionVoltageInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_protectionVoltageInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        # 设置输出电流输入框为单行模式
        self.w_outputCurrentInput.setMaximumHeight(30)
        self.w_outputCurrentInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_outputCurrentInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_outputCurrentInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        # 调整文本输入框字体大小和边距
        self.w_protectionVoltageInput.setStyleSheet("""
                            QTextEdit {
                                padding: 0px;     /* 减少内边距 */
                                margin: 0px;      /* 减少外边距 */
                            }
                        """)
        self.w_outputCurrentInput.setStyleSheet("""
                            QTextEdit {
                                padding: 0px;
                                margin: 0px;
                            }
                        """)
        # 设置复选框样式
        self.w_OutputCheck.setStyleSheet("""
                                    QCheckBox {
                                        color: #39c5bb;
                                    }
                                """)
        # 初始化电流源模式保护电压默认值10V 默认输出电流0
        self.w_protectionVoltageInput.setPlainText("10")
        self.w_chooseSizeOfProtectionVoltage.setCurrentIndex(0)
        self.w_outputCurrentInput.setPlainText("0")

        # 连接电流源信号
        self.w_save2table_2.clicked.connect(self.save_current_data)
        self.w_OutputCheck.stateChanged.connect(self.toggle_current_output)
        self.w_ConfirmCurrentModeSettings.clicked.connect(self.set_protection_voltage)
        self.w_ConfirmCurrentModeSettings.clicked.connect(self.set_target_current)
        self.w_OutputON.clicked.connect(self.resume_current_measurement)
        self.w_OutputOFF.clicked.connect(self.pause_current_measurement)



    def set_protection_voltage(self):       # 按下确定键后，设置保护电压大小
        try:
            value = float(self.w_protectionVoltageInput.toPlainText())
            unit = self.w_chooseSizeOfProtectionVoltage.currentText()
            multiplier = {
                'm': 1e-3,
                'u': 1e-6,
                'n': 1e-9
            }.get(unit, 1)
            self.keithley.setVoltageProtection(value * multiplier)
            QMessageBox.information(self, "成功", "保护电压设置成功!")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def set_target_current(self):               # 按下确定键后，设置目标输出电流大小
        try:
            value = float(self.w_outputCurrentInput.toPlainText())
            unit = self.w_comboBox_3.currentText()
            multiplier = {
                'm':1e-3,
                'u':1e-6,
                'n':1e-9
            }.get(unit, 1)
            target_curr = value * multiplier
            # 启动电流源线程
            self.current_thread = CurrentThread(self.keithley, target_curr)
            self.current_thread.finished.connect(lambda: (
                QMessageBox.information(self, "完成", "电流设置完成!"),
                self.current_plot_widget.loadData(),
                self.update_current_measurements()
            ))
            self.current_thread.error.connect(
                lambda e: QMessageBox.critical(self, "错误", e))
            self.current_thread.start()
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def update_current_measurements(self): # 更新当前测量数值
        try:
            if not self.keithley.get_output_state():
                self.w_voltageDisplay.setText("N/A")
                self.current_mode_data = None
                return
            # 读取当前测量值
            voltage = self.keithley.showVoltage()
            current = self.keithley.showCurrent()
            # 更新界面上关于当前电压的显示
            self.w_voltageDisplay.setText(f"{voltage:.4f}")
            # 存储当前数值，但不自动添加到DataFrame中
            self.current_mode_data = {
                "Timestamp": pd.Timestamp.now(),
                "Current(A)": current,
                "Voltage(V)": voltage,
                "备注": ""
            }
        except Exception as e:
            print(f"电流源测量更新错误: {str(e)}")

    def save_current_data(self):        # 存储当前数值到excel表格中
        if self.current_mode_data is None:
            QMessageBox.warning(self, "警告", "无可用数据!")
            return

        self.current_plot_widget.df = pd.concat(
            [self.current_plot_widget.df, pd.DataFrame([self.current_mode_data])],
            ignore_index=True
        )
        # 同步表格数据并保存
        self.current_plot_widget.sync_table_data()
        try:
            self.current_plot_widget.save_to_excel("Log_SourceIData.xlsx")
            QMessageBox.information(self, "成功", "数据保存成功!")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
        # 更新图表和表格显示
        self.current_plot_widget.updatePlot()
        self.current_plot_widget.updateView()

    def toggle_current_output(self, state):
        try:
            if state == Qt.Checked:
                self.keithley.outputOn()
            else:
                self.keithley.outputOff()
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
            # 恢复复选框状态
            with QtCore.QSignalBlocker(self.w_OutputCheck):
                self.w_OutputCheck.setChecked(not state)


    def pause_current_measurement(self):
        self.keithley.outputOff()
        self.current_plot_widget.loadData()

    def resume_current_measurement(self):
        self.keithley.outputOn()
        self.current_plot_widget.loadData()


    ####################################################### 2430电流源模式相关函数 ####################################################

    def init2430_current_mode(self):
        # 电流源绘图部件
        self.kei2430_current_plot_widget = currentPlotWidget2430()
        layout_current = QVBoxLayout(self.w_2430SourceIcurrentPlot)
        layout_current.addWidget(self.kei2430_current_plot_widget)
        # 设置保护电压输入框为单行模式
        self.w_2430SourceIVoltageProtectionInput.setMaximumHeight(30)
        self.w_2430SourceIVoltageProtectionInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430SourceIVoltageProtectionInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430SourceIVoltageProtectionInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        # 设置输出电流输入框为单行模式
        self.w_2430SourceIOutputCurrentInput.setMaximumHeight(30)
        self.w_2430SourceIOutputCurrentInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430SourceIOutputCurrentInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430SourceIOutputCurrentInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        # 调整文本输入框字体大小和边距
        self.w_2430SourceIVoltageProtectionInput.setStyleSheet("""
                            QTextEdit {
                                padding: 0px;     /* 减少内边距 */
                                margin: 0px;      /* 减少外边距 */
                            }
                        """)
        self.w_2430SourceIOutputCurrentInput.setStyleSheet("""
                            QTextEdit {
                                padding: 0px;
                                margin: 0px;
                            }
                        """)
        # 设置复选框样式
        self.w_2430SourceIOutputCheck.setStyleSheet("""
                                    QCheckBox {
                                        color: #39c5bb;
                                    }
                                """)
        # 连接电流源信号
        self.w_2430SourceIsave2table.clicked.connect(self.save2430_current_data)
        self.w_2430SourceIOutputCheck.stateChanged.connect(self.toggle2430_current_output)
        self.w_2430ConfirmSourceIOutput.clicked.connect(self.set2430_protection_voltage)
        self.w_2430ConfirmSourceIOutput.clicked.connect(self.set2430_target_current)
        self.w_2430SourceIOutputOn.clicked.connect(self.resume2430_current_measurement)
        self.w_2430SourceIOutputOff.clicked.connect(self.pause2430_current_measurement)
        #
        # self.timer2430MainThread()


    def set2430_protection_voltage(self):       # 按下确定键后，设置保护电压大小
        try:
            value = float(self.w_2430SourceIVoltageProtectionInput.toPlainText())
            unit = self.w_2430chooseSizeOfSOurceVProtectionVoltage.currentText()
            multiplier = {
                'm': 1e-3,
                'u': 1e-6,
                'n': 1e-9
            }.get(unit, 1)
            self.keithley2430.setVoltageProtection(value * multiplier)
            QMessageBox.information(self, "成功", "保护电压设置成功!")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def set2430_target_current(self):               # 按下确定键后，设置目标输出电流大小 ##################################
        try:
            value = float(self.w_2430SourceIOutputCurrentInput.toPlainText())
            unit = self.w_2430chooseSizeOfSourceIOutputCurrentInput.currentText()
            multiplier = {
                'm':1e-3,
                'u':1e-6,
                'n':1e-9
            }.get(unit, 1)
            target_curr = value * multiplier
            # 输入验证
            if abs(target_curr) > 3:  # 假设2430最大电流1.05A
                raise ValueError("超出电流安全范围")
            # 启动电流源线程
            self.current_thread2430 = Current2430Thread(self.keithley2430, target_curr)
            self.current_thread2430.finished.connect(lambda: (
                QMessageBox.information(self, "完成", "2430电流设置完成!"),
                self.kei2430_current_plot_widget.loadData(),
                self.update2430_current_measurements(),
                self.check2430_output_state()
            ))
            self.current_thread2430.error.connect(
                lambda e: QMessageBox.critical(self, "错误", e))
            self.current_thread2430.start()
        except ValueError as ve:
            QMessageBox.critical(self, "输入错误", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"未知错误: {str(e)}")

    def update2430_current_measurements(self): # 更新当前测量数值
        try:
            if not self.keithley2430.get_output_state():
                self.w_2430SourceIvoltageDisplay.setText("N/A")
                self.current2430_mode_data = None
                return
            # 读取当前测量值
            voltage = self.keithley2430.showVoltage()
            current = self.keithley2430.showCurrent()
            # 更新界面上关于当前电压的显示
            self.w_2430SourceIvoltageDisplay.setText(f"{voltage:.4f}")
            # 存储当前数值，但不自动添加到DataFrame中
            self.current2430_mode_data = {
                "Timestamp": pd.Timestamp.now(),
                "Current(A)": current,
                "Voltage(V)": voltage,
                "备注": ""
            }
        except Exception as e:
            print(f"电流源测量更新错误: {str(e)}")

    def save2430_current_data(self):        # 存储当前数值到excel表格中
        if self.current2430_mode_data is None:
            QMessageBox.warning(self, "警告", "无可用数据!")
            return

        self.kei2430_current_plot_widget.df = pd.concat(
            [self.kei2430_current_plot_widget.df, pd.DataFrame([self.current2430_mode_data])],
            ignore_index=True
        )
        # 同步表格数据并保存
        self.kei2430_current_plot_widget.sync_table_data()
        try:
            self.kei2430_current_plot_widget.save_to_excel()
            QMessageBox.information(self, "成功", "数据保存成功!")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
        # 更新图表和表格显示
        self.kei2430_current_plot_widget.updatePlot()
        self.kei2430_current_plot_widget.updateView()

    def toggle2430_current_output(self, state):
        try:
            if state == Qt.Checked:
                self.keithley2430.outputOn()
            else:
                self.keithley2430.outputOff()
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
            # 恢复复选框状态
            with QtCore.QSignalBlocker(self.w_2430SourceIOutputCheck):
                self.w_2430SourceIOutputCheck.setChecked(not state)

    def pause2430_current_measurement(self):
        if hasattr(self, 'current_thread2430') and self.current_thread2430.isRunning():
            self.current_thread2430.quit()
            self.current_thread2430.wait()
            time.sleep(0.1)
        try:
            self.keithley2430.outputOff()  # 确保输出关闭
        except Exception as e:
            QMessageBox.critical(self, "错误", f"关闭输出失败: {str(e)}")
        self.check2430_output_state()  # 更新UI状态

    def resume2430_current_measurement(self):
        try:
            self.keithley2430.outputOn()
            if not hasattr(self, 'current_thread2430') or not self.current_thread2430.isRunning():
                self.current_thread2430 = Current2430Thread(
                    self.keithley2430,
                    self.keithley2430.showCurrent()  # 获取当前设定值
                )
                self.current_thread2430.start()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"重启输出失败: {str(e)}")
        self.check2430_output_state()  # 更新UI状态


    ####################################################### 脉冲模式相关函数 #####################################################
    def init_pulse_mode(self):      # 初始化脉冲模式绘图组件、连接信号
        # 替换初始化脉冲预览部件
        self.pulse_preview = PulsePreviewWidget()
        layout_preview = QVBoxLayout(self.currentPlot_2)
        layout_preview.addWidget(self.pulse_preview)
        # 设置脉冲宽度输入框为单行模式
        self.w_PulseWidthInput.setMaximumHeight(30)
        self.w_PulseWidthInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_PulseWidthInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_PulseWidthInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_PulseWidthInput.setStyleSheet("""
                                    QTextEdit {
                                        padding: 0px;     /* 减少内边距 */
                                        margin: 0px;      /* 减少外边距 */
                                    }
                                """)
        # 设置占空比输入框为单行模式
        self.w_PulseDutyCycleInput.setMaximumHeight(30)
        self.w_PulseDutyCycleInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_PulseDutyCycleInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_PulseDutyCycleInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_PulseDutyCycleInput.setStyleSheet("""
                                            QTextEdit {
                                                padding: 0px;     /* 减少内边距 */
                                                margin: 0px;      /* 减少外边距 */
                                            }
                                        """)
        # 设置高电平输入框为单行模式
        self.w_InputPulseHighLevel.setMaximumHeight(30)
        self.w_InputPulseHighLevel.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_InputPulseHighLevel.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_InputPulseHighLevel.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_InputPulseHighLevel.setStyleSheet("""
                                                    QTextEdit {
                                                        padding: 0px;     /* 减少内边距 */
                                                        margin: 0px;      /* 减少外边距 */
                                                    }
                                                """)
        # 设置低电平输入框为单行模式
        self.w_InputPulseLowLevel.setMaximumHeight(30)
        self.w_InputPulseLowLevel.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_InputPulseLowLevel.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_InputPulseLowLevel.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_InputPulseLowLevel.setStyleSheet("""
                                                            QTextEdit {
                                                                padding: 0px;     /* 减少内边距 */
                                                                margin: 0px;      /* 减少外边距 */
                                                            }
                                                        """)
        # 连接预览按钮
        self.w_PreviewPulse.clicked.connect(self.generate_pulse_preview)
        # 初始化表格样式
        self.tableWidget.horizontalHeader().setStyleSheet(
            "QHeaderView::section { background-color: #607D8B; color: white; }")
        self.tableWidget.verticalHeader().setVisible(False)

    def generate_pulse_preview(self):       # 生成脉冲预览
        try:
            # 获取当前脉冲模式参数 基础/阶梯/自定义
            current_tab = self.tabWidget_2.currentIndex()
            params = {}
            if current_tab == 0:  # 模式1
                params = {
                    'high': float(self.w_InputPulseHighLevel.toPlainText()),
                    'low': float(self.w_InputPulseLowLevel.toPlainText()),
                    'width': float(self.w_PulseWidthInput.toPlainText()) * self.get_unit_multiplier(
                        self.w_chooseSizeOfPulseWidth.currentText()),
                    'duty': float(self.w_PulseDutyCycleInput.toPlainText()),
                    'num': self.w_numberOfPulse.value()
                }
            elif current_tab == 1:  # 模式2
                params = {
                    'high': float(self.w_InputPulseHighLevel_2.toPlainText()),
                    'low': float(self.w_InputPulseLowLevel_2.toPlainText()),
                    'width': float(self.w_PulseWidthInput_2.toPlainText()) * self.get_unit_multiplier(
                        self.w_chooseSizeOfPulseWidth_3.currentText()),
                    'duty': float(self.w_PulseDutyCycleInput_2.toPlainText()),
                    'num': self.w_numberOfPulse_2.value()
                }

            # 更新预览
            self.pulse_preview.update_preview(params)

        except ValueError as ve:
            QMessageBox.critical(self, "输入错误", f"无效的数值输入: {str(ve)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成预览失败: {str(e)}")

    def get_unit_multiplier(self, unit):
        """单位转换"""
        return {
            'm': 1e-3,
            'u': 1e-6,
            'n': 1e-9,
            '': 1  # 默认无单位
        }.get(unit, 1)

    ####################################################### 2430脉冲模式相关函数 #####################################################

    def init2430_pulse_mode(self):      # 初始化脉冲模式绘图组件、连接信号
        # # 替换初始化脉冲预览部件
        self.pulse2430_preview = PulsePreviewWidget2430()
        layout_preview = QVBoxLayout(self.w_2430Pulse_previewPlot)
        layout_preview.addWidget(self.pulse2430_preview)
        # # 替换脉冲输出结果表格
        self.pulse2430_result = PulseResultWidget2430()
        layout_preview = QVBoxLayout(self.w_2430Pulse_MeasurePlot)
        layout_preview.addWidget(self.pulse2430_result)
        # 设置脉冲宽度输入框为单行模式
        self.w_2430Pulse1_pulseWidth_Input.setMaximumHeight(30)
        self.w_2430Pulse1_pulseWidth_Input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430Pulse1_pulseWidth_Input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430Pulse1_pulseWidth_Input.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_2430Pulse1_pulseWidth_Input.setStyleSheet("""
                                    QTextEdit {
                                        padding: 0px;     /* 减少内边距 */
                                        margin: 0px;      /* 减少外边距 */
                                    }
                                """)
        # 设置保护电压电流输入框为单行模式
        self.w_2430Pulse1_protectionIV_input.setMaximumHeight(30)
        self.w_2430Pulse1_protectionIV_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430Pulse1_protectionIV_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430Pulse1_protectionIV_input.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_2430Pulse1_protectionIV_input.setStyleSheet("""
                                            QTextEdit {
                                                padding: 0px;     /* 减少内边距 */
                                                margin: 0px;      /* 减少外边距 */
                                            }
                                        """)
        # 设置脉冲强度输入框为单行模式
        self.w_2430Pulse1_InputPulseHighLevel.setMaximumHeight(30)
        self.w_2430Pulse1_InputPulseHighLevel.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430Pulse1_InputPulseHighLevel.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430Pulse1_InputPulseHighLevel.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_2430Pulse1_InputPulseHighLevel.setStyleSheet("""
                                                    QTextEdit {
                                                        padding: 0px;     /* 减少内边距 */
                                                        margin: 0px;      /* 减少外边距 */
                                                    }
                                                """)
        # 设置脉冲延时输入框为单行模式
        self.w_2430Pulse1_PulseDelay_Input.setMaximumHeight(30)
        self.w_2430Pulse1_PulseDelay_Input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430Pulse1_PulseDelay_Input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430Pulse1_PulseDelay_Input.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_2430Pulse1_PulseDelay_Input.setStyleSheet("""
                                                            QTextEdit {
                                                                padding: 0px;     /* 减少内边距 */
                                                                margin: 0px;      /* 减少外边距 */
                                                            }
                                                        """)
        # 设置脉冲扫描宽度输入框为单行模式
        self.w_2430PulseSweepWidthInput.setMaximumHeight(30)
        self.w_2430PulseSweepWidthInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430PulseSweepWidthInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430PulseSweepWidthInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_2430PulseSweepWidthInput.setStyleSheet("""
                                                                    QTextEdit {
                                                                        padding: 0px;     /* 减少内边距 */
                                                                        margin: 0px;      /* 减少外边距 */
                                                                    }
                                                                """)
        # 设置脉冲扫描宽度输入框为单行模式
        self.w_2430PulseSweepDelayInput.setMaximumHeight(30)
        self.w_2430PulseSweepDelayInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430PulseSweepDelayInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430PulseSweepDelayInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_2430PulseSweepDelayInput.setStyleSheet("""
                                                                            QTextEdit {
                                                                                padding: 0px;     /* 减少内边距 */
                                                                                margin: 0px;      /* 减少外边距 */
                                                                            }
                                                                        """)
        # 设置脉冲扫描起始电平输入框为单行模式
        self.w_2430PulseSweepStartLevelInput.setMaximumHeight(30)
        self.w_2430PulseSweepStartLevelInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430PulseSweepStartLevelInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430PulseSweepStartLevelInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_2430PulseSweepStartLevelInput.setStyleSheet("""
                                                                                    QTextEdit {
                                                                                        padding: 0px;     /* 减少内边距 */
                                                                                        margin: 0px;      /* 减少外边距 */
                                                                                    }
                                                                                """)
        # 设置脉冲扫描终止电平输入框为单行模式
        self.w_2430PulseSweepStopLevelInput.setMaximumHeight(30)
        self.w_2430PulseSweepStopLevelInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430PulseSweepStopLevelInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430PulseSweepStopLevelInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_2430PulseSweepStopLevelInput.setStyleSheet("""
                                                                                            QTextEdit {
                                                                                                padding: 0px;     /* 减少内边距 */
                                                                                                margin: 0px;      /* 减少外边距 */
                                                                                            }
                                                                                        """)
        # 设置脉冲扫描步长输入框为单行模式
        self.w_2430PulseSweepStepLevelInput.setMaximumHeight(30)
        self.w_2430PulseSweepStepLevelInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430PulseSweepStepLevelInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430PulseSweepStepLevelInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_2430PulseSweepStepLevelInput.setStyleSheet("""
                                                                                                    QTextEdit {
                                                                                                        padding: 0px;     /* 减少内边距 */
                                                                                                        margin: 0px;      /* 减少外边距 */
                                                                                                    }
                                                                                                """)
        # 设置脉冲扫描保护输入框为单行模式
        self.w_2430PulseSweepProtectionInput.setMaximumHeight(30)
        self.w_2430PulseSweepProtectionInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430PulseSweepProtectionInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430PulseSweepProtectionInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_2430PulseSweepProtectionInput.setStyleSheet("""
                                                                                                            QTextEdit {
                                                                                                                padding: 0px;     /* 减少内边距 */
                                                                                                                margin: 0px;      /* 减少外边距 */
                                                                                                            }
                                                                                                        """)


        # 连接信号
        self.w_2430Pulse_preview.clicked.connect(self.generate_2430pulse_preview)       # 预览按钮
        self.w_2430Pulse_OutputOn.clicked.connect(self.kei2430Pulse_outputOn)           # 输出按钮
        self.w_2430Pulse_OutputOff.clicked.connect(self.kei2430Pulse_outputOff)         # 停止按钮
        self.w_2430PulseModeChoice.currentChanged.connect(self.change2430PulseMode)     # 模式切换
        self.w_2430Pulse_choosePulseSource.currentIndexChanged.connect(self.change2430PulseSource)     # source切换


        # 设置基础模式默认值
        self.w_2430Pulse1_pulseWidth_Input.setPlainText("5")    # 脉冲宽度默认值5
        self.w_2430Pulse1_protectionIV_input.setPlainText("1")  # 保护电流1
        self.w_2430Pulse1_InputPulseHighLevel.setPlainText("1")  # 脉冲强度1
        self.w_2430Pulse1_PulseDelay_Input.setPlainText("3")  # 脉冲延时
        # 设置基础模式单位默认值
        self.w_2430chooseSizeOfPulseWidth1.setCurrentIndex(1)  # 脉冲宽度单位ms
        self.w_2430chooseSizeOfProtectionIV1.setCurrentIndex(0)  # 终止单位V
        self.w_2430chooseSizeOfPulseHighLevel1.setCurrentIndex(0)  # 电流保护单位A
        self.w_2430chooseSizeOfPulseDelay1.setCurrentIndex(1)  # 延时单位ms
        # 设置阶梯模式默认值
        self.w_2430PulseSweepWidthInput.setPlainText("5")  # 脉冲宽度默认值5
        self.w_2430PulseSweepDelayInput.setPlainText("3")  # 脉冲延时默认值3
        self.w_2430PulseSweepStartLevelInput.setPlainText("0")  # 起始电平默认值0
        self.w_2430PulseSweepStopLevelInput.setPlainText("5")  # 终止电平默认值5
        self.w_2430PulseSweepStepLevelInput.setPlainText("1")  # 步长默认值1
        self.w_2430PulseSweepProtectionInput.setPlainText("1")  # 保护默认值1
        # 设置阶梯模式单位默认值
        self.w_2430chooseSizeOfPulseSweepWidth.setCurrentIndex(1)  # 脉冲宽度单位ms
        self.w_2430chooseSizeOfPulseSweepDelay.setCurrentIndex(1)  # 脉冲延时单位ms
        self.w_2430chooseSizeOfPulseSweeStartLevel.setCurrentIndex(0)  # 起始电平单位V
        self.w_2430chooseSizeOfPulseSweepStopLevel.setCurrentIndex(0)  # 终止电平单位V
        self.w_2430chooseSizeOfPulseSweepStepLevel.setCurrentIndex(0)  # 步长单位V
        self.w_2430chooseSizeOfPulseSweepProtection.setCurrentIndex(0)  # 保护默认值1A

        self.w_2430chooseSizeOfPulseSweepWidth.setCurrentIndex(1)

        # 设置模式默认值
        self.w_2430Pulse_choosePulseSource.setCurrentIndex(1)  # 电压脉冲

        # 初始化UI
        self.change2430PulseSource()


    def generate_2430pulse_preview(self):

        current_tab = self.w_2430PulseModeChoice.currentIndex()
        if current_tab == 0: # 基础
            print("preview1")
            try:
                # 获取当前选择的脉冲源
                currentMode = self.w_2430Pulse_choosePulseSource.currentText()

                # 获取用户输入参数
                params = {
                    'pulse_width': float(self.w_2430Pulse1_pulseWidth_Input.toPlainText()) * self.get_unit_multiplier(self.w_2430chooseSizeOfPulseWidth1.currentText()),  # 脉冲宽度
                    'pulse_delay': float(self.w_2430Pulse1_PulseDelay_Input.toPlainText()) * self.get_unit_multiplier(self.w_2430chooseSizeOfPulseDelay1.currentText()),  # 脉冲延迟
                    'trigger_count': int(self.w_2430Pulse1_triggerCount.value()),  # 触发次数
                    'arm_count': int(self.w_2430Pulse1_armCount_input.value()),  # 臂计数
                    'high_level': float(self.w_2430Pulse1_InputPulseHighLevel.toPlainText()) * self.get_unit_multiplier(self.w_2430chooseSizeOfPulseHighLevel1.currentText()),  # 高电平值
                    'source_mode': 'current' if "电流" in currentMode else 'voltage',  # 源模式
                    'meas_ref_zero': False
                }
                # 更新预览组件
                self.pulse2430_preview.update_preview(params)

            except ValueError as ve:
                QMessageBox.warning(self, "参数错误", str(ve))
            except Exception as e:
                QMessageBox.critical(self, "生成错误", f"无法生成预览: {str(e)}")

        elif current_tab == 1:
            try:
                print("preview2")

                # 获取用户输入参数
                params = {
                    'PulseWidth': float(self.w_2430PulseSweepWidthInput.toPlainText()) * self.get_unit_multiplier(
                        self.w_2430chooseSizeOfPulseSweepWidth.currentText()),
                    'Delay': float(self.w_2430PulseSweepDelayInput.toPlainText()) * self.get_unit_multiplier(
                        self.w_2430chooseSizeOfPulseSweepDelay.currentText()),
                    'SourceMode': 'current' if "电流" in self.w_2430Pulse_choosePulseSource.currentText() else 'voltage',
                    'StartLevel': float(self.w_2430PulseSweepStartLevelInput.toPlainText()) * self.get_unit_multiplier(
                        self.w_2430chooseSizeOfPulseSweeStartLevel.currentText()),
                    'StopLevel': float(self.w_2430PulseSweepStopLevelInput.toPlainText()) * self.get_unit_multiplier(
                        self.w_2430chooseSizeOfPulseSweepStopLevel.currentText()),
                    'StepLevel': float(self.w_2430PulseSweepStepLevelInput.toPlainText()) * self.get_unit_multiplier(
                        self.w_2430chooseSizeOfPulseSweepStepLevel.currentText())
                }
                # 更新预览组件
                self.pulse2430_preview.update_sweep_preview(params)

            except ValueError as ve:
                QMessageBox.warning(self, "参数错误", str(ve))
            except Exception as e:
                QMessageBox.critical(self, "生成错误", f"无法生成预览: {str(e)}")

    def kei2430Pulse_outputOn(self):

        current_tab = self.w_2430PulseModeChoice.currentIndex()
        if current_tab == 0:  # 基础脉冲
            try:
                # 获取输入参数
                params = {
                    'pulse_width': float(self.w_2430Pulse1_pulseWidth_Input.toPlainText()) * self.get_unit_multiplier(self.w_2430chooseSizeOfPulseWidth1.currentText()),
                    'pulse_delay': float(self.w_2430Pulse1_PulseDelay_Input.toPlainText()) * self.get_unit_multiplier(self.w_2430chooseSizeOfPulseDelay1.currentText()),
                    'arm_count': int(self.w_2430Pulse1_armCount_input.value()),
                    'trigger_count': int(self.w_2430Pulse1_triggerCount.value()),
                    'source_mode': 'current' if "电流" in self.w_2430Pulse_choosePulseSource.currentText() else 'voltage',
                    'high_level': float(self.w_2430Pulse1_InputPulseHighLevel.toPlainText()) * self.get_unit_multiplier(self.w_2430chooseSizeOfPulseHighLevel1.currentText()),
                    'current_protection': float(self.w_2430Pulse1_protectionIV_input.toPlainText()) * self.get_unit_multiplier(self.w_2430chooseSizeOfProtectionIV1.currentText()),
                    'voltage_protection': float(self.w_2430Pulse1_protectionIV_input.toPlainText()) * self.get_unit_multiplier(self.w_2430chooseSizeOfProtectionIV1.currentText())
                }
                # 输入验证
                # if params['pulse_width'] < 4e-6:
                #     raise ValueError("脉冲宽度不能小于4μs")
                # if params['high_level'] > (3 if params['source_mode'] == 'current' else 1000):
                #     raise ValueError("输出电平超出安全范围")
                # 启动脉冲输出
                self.keithley2430.PulseMode2430(
                    PulseWidth=params['pulse_width'],
                    Delay=params['pulse_delay'],
                    ArmCount=params['arm_count'],
                    TriggerCount=params['trigger_count'],
                    SourceMode=params['source_mode'],
                    HighLevel=params['high_level'],
                    CurrentProtection=params['current_protection'],
                    VoltageProtection=params['voltage_protection']
                )
                # 保存扫描数据
                if params['source_mode'] == 'current':
                    self.keithley2430.savePulseData(sheetname='IPulse')
                else:
                    self.keithley2430.savePulseData(sheetname='VPulse')
            except Exception as e:
                QMessageBox.critical(self, "参数错误", str(e))

        elif current_tab == 1:  # 脉冲扫描
            print("tab1")
            try:
                params = {
                    'pulse_width': float(self.w_2430PulseSweepWidthInput.toPlainText()) * self.get_unit_multiplier(
                        self.w_2430chooseSizeOfPulseSweepWidth.currentText()),
                    'pulse_delay': float(self.w_2430PulseSweepDelayInput.toPlainText()) * self.get_unit_multiplier(
                        self.w_2430chooseSizeOfPulseSweepDelay.currentText()),
                    'source_mode': 'current' if "电流" in self.w_2430Pulse_choosePulseSource.currentText() else 'voltage',
                    'start_level': float(self.w_2430PulseSweepStartLevelInput.toPlainText()) * self.get_unit_multiplier(
                        self.w_2430chooseSizeOfPulseSweeStartLevel.currentText()),
                    'stop_level': float(self.w_2430PulseSweepStopLevelInput.toPlainText()) * self.get_unit_multiplier(
                        self.w_2430chooseSizeOfPulseSweepStopLevel.currentText()),
                    'step_level': float(self.w_2430PulseSweepStepLevelInput.toPlainText()) * self.get_unit_multiplier(
                        self.w_2430chooseSizeOfPulseSweepStepLevel.currentText()),
                    'protection': float(self.w_2430PulseSweepProtectionInput.toPlainText()) * self.get_unit_multiplier(
                        self.w_2430chooseSizeOfPulseSweepProtection.currentText())
                }
                # print(params)
                # 输入验证
                dutyCycle = params['pulse_width'] / (params['pulse_width']+params['pulse_delay'])
                print(dutyCycle)
                if params['pulse_width'] < 150e-6:
                    raise ValueError("脉冲宽度不能小于150μs")
                if params['pulse_width'] > 5e-3:
                    raise ValueError("脉冲宽度不能大于5ms")
                # if params['high_level'] > (5 if params['source_mode'] == 'current' else 1000):
                #     raise ValueError("输出电平超出安全范围")
                # if dutyCycle > 0.08:
                #     raise ValueError("占空比需小于8%")
                # 启动脉冲输出
                self.keithley2430.PulseSweepMode2430(
                    PulseWidth=params['pulse_width'],
                    Delay=params['pulse_delay'],
                    SourceMode=params['source_mode'],
                    StartLevel=params['start_level'],
                    StopLevel=params['stop_level'],
                    StepLevel=params['step_level'],
                    CurrentProtection=params['protection'],
                    VoltageProtection=params['protection']
                )
                # 保存扫描数据
                if params['source_mode'] == 'current':
                    self.keithley2430.savePulseData(sheetname='IPulse')
                else:
                    self.keithley2430.savePulseData(sheetname='VPulse')
            except Exception as e:
                QMessageBox.critical(self, "参数错误", str(e))

    def kei2430Pulse_outputOff(self):
        pass

    def change2430PulseMode(self):
        if self.keithley2430 is None:
            return



    def change2430PulseSource(self):
        currentMode = self.w_2430Pulse_choosePulseSource.currentText()

        if currentMode == "电流脉冲":
            # 更新单位为A
            self.w_label_percent_3.setText("V")
            self.w_label_VA_PulseHighLevel_3.setText("A")
            self.w_labelDutyCycle_3.setText("保护电压")

            self.w_label_VA_PulseHighLevel_4.setText("A")
            self.w_label_VA_PulseLowLevel_5.setText("A")
            self.w_label_VA_PulseLowLevel_6.setText("A")
            self.w_label_VA_PulseLowLevel_7.setText("V")
            self.w_label_PulseLowLevel_7.setText("保护电压")

        else:
            # 更新单位为V
            self.w_label_percent_3.setText("A")
            self.w_label_VA_PulseHighLevel_3.setText("V")
            self.w_labelDutyCycle_3.setText("保护电流")
            self.w_label_VA_PulseHighLevel_4.setText("V")
            self.w_label_VA_PulseLowLevel_5.setText("V")
            self.w_label_VA_PulseLowLevel_6.setText("V")
            self.w_label_VA_PulseLowLevel_7.setText("A")
            self.w_label_PulseLowLevel_7.setText("保护电流")





#######################################################扫描模式相关函数#####################################################

    def init_scanning_mode(self):
        """初始化扫描模式控件"""
        # 替换扫描结果组件
        self.sweepResult = SweepWidget()
        layout_preview = QVBoxLayout(self.sweepResultWidget)
        layout_preview.addWidget(self.sweepResult)
        # 设置默认值
        self.w_SweepStartInput.setPlainText("0")
        self.w_SweepEndInput.setPlainText("10")  # 终止值
        self.w_SweepStepInput.setPlainText("1")  # 步数
        self.w_SweepIVProtectionInput.setPlainText("10")  # 电压保护
        self.w_SweepDelayInput.setPlainText("1")  # 测量延时
        # 设置单位默认值
        self.w_chooseSizeOfStartInput.setCurrentIndex(1)  # 起始单位
        self.w_chooseSizeOfEndInput.setCurrentIndex(1)  # 终止单位
        self.w_chooseSizeOfSweepIVProtection.setCurrentIndex(0)  # 电压保护单位
        self.w_chooseSizeOfSweepDelay.setCurrentIndex(0)  # 测量延时单位
        # 设置模式默认值
        self.w_chooseSourceOfSweep.setCurrentIndex(0)  # 电流扫描
        self.w_chooseTypeOfSweep.setCurrentIndex(0)  # 线性扫描
        # 设置输输入框为单行模式
        self.w_SweepStartInput.setMaximumHeight(30)
        self.w_SweepStartInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_SweepStartInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_SweepStartInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_SweepEndInput.setMaximumHeight(30)
        self.w_SweepEndInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_SweepEndInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_SweepEndInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_SweepStepInput.setMaximumHeight(30)
        self.w_SweepStepInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_SweepStepInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_SweepStepInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_SweepIVProtectionInput.setMaximumHeight(30)
        self.w_SweepIVProtectionInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_SweepIVProtectionInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_SweepIVProtectionInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_SweepDelayInput.setMaximumHeight(30)
        self.w_SweepDelayInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_SweepDelayInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_SweepDelayInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        # 调整输入框字体大小和边距
        self.w_SweepStartInput.setStyleSheet("""
                                    QTextEdit {
                                        padding: 0px;     /* 减少内边距 */
                                        margin: 0px;      /* 减少外边距 */
                                    }
                                """)
        self.w_SweepEndInput.setStyleSheet("""
                                            QTextEdit {
                                                padding: 0px;     /* 减少内边距 */
                                                margin: 0px;      /* 减少外边距 */
                                            }
                                        """)
        self.w_SweepStepInput.setStyleSheet("""
                                                    QTextEdit {
                                                        padding: 0px;     /* 减少内边距 */
                                                        margin: 0px;      /* 减少外边距 */
                                                    }
                                                """)
        self.w_SweepIVProtectionInput.setStyleSheet("""
                                                            QTextEdit {
                                                                padding: 0px;     /* 减少内边距 */
                                                                margin: 0px;      /* 减少外边距 */
                                                            }
                                                        """)
        self.w_SweepDelayInput.setStyleSheet("""
                                                                    QTextEdit {
                                                                        padding: 0px;     /* 减少内边距 */
                                                                        margin: 0px;      /* 减少外边距 */
                                                                    }
                                                                """)
        # 连接信号
        self.w_ConfirmSweepModeSettings.clicked.connect(self.start_scanning)
        self.w_chooseTypeOfSweep.currentIndexChanged.connect(self.toggle_sweep_mode)
        self.w_chooseSourceOfSweep.currentIndexChanged.connect(self.toggle_source_mode)
        # 初始化标签显示
        self.toggle_source_mode(0)  # 默认电流源
        self.toggle_sweep_mode(0)  # 默认线性扫描
        # 初始化扫描线程
        self.scan_thread = None
        self.scanning = False

    def toggle_sweep_mode(self, index):
        """切换线性/对数扫描模式"""
        if index == 0:  # 线性扫描
            self.w_label_SweepStepPoint.setText("步长:")
            self.w_SweepStepInput.setPlaceholderText("1")
            self.w_chooseSizeOfStepInput.setCurrentIndex(1)
        else:  # 对数扫描
            self.w_label_SweepStepPoint.setText("点数(≥2):")
            self.w_SweepStepInput.setPlaceholderText("10")
            self.w_chooseSizeOfStepInput.setCurrentIndex(0)

    def toggle_source_mode(self, index):
        """切换源模式时更新单位标签"""
        # 0-电流源 1-电压源
        if index == 0:
            self.w_label_seconds_6.setText("A")
            self.w_label_seconds_5.setText("A")
            self.w_label_seconds_4.setText("V")
            self.w_label_seconds_7.setText("A")
            self.w_label_IVProtection.setText("电压保护：")
        else:
            self.w_label_seconds_6.setText("V")
            self.w_label_seconds_5.setText("V")
            self.w_label_seconds_4.setText("A")
            self.w_label_seconds_7.setText("V")
            self.w_label_IVProtection.setText("电流保护：")

    def start_scanning(self):
        try:
            # 获取扫描参数
            source_mode = self.w_chooseSourceOfSweep.currentIndex()  # 0-电流源 1-电压源
            sweep_type = 'linear' if self.w_chooseTypeOfSweep.currentIndex() == 0 else 'log'

            # 单位转换函数
            def get_unit_value(text_edit, combo_box):
                value = float(text_edit.toPlainText())
                unit = combo_box.currentText()
                multiplier = {
                    'n': 1e-9,
                    'u': 1e-6,
                    'm': 1e-3,
                    '': 1
                }.get(unit, 1)
                return value * multiplier

            # 参数收集
            config = {
                'sweep_type': sweep_type,
                'start': get_unit_value(self.w_SweepStartInput, self.w_chooseSizeOfStartInput),
                'stop': get_unit_value(self.w_SweepEndInput, self.w_chooseSizeOfEndInput),
                'step': get_unit_value(self.w_SweepStepInput, self.w_chooseSizeOfStepInput),
                'points': int(self.w_SweepStepInput.toPlainText()),
                'protection': get_unit_value(self.w_SweepIVProtectionInput, self.w_chooseSizeOfSweepIVProtection),
                'delay': get_unit_value(self.w_SweepDelayInput, self.w_chooseSizeOfSweepDelay)
            }

            print(config)

            # 输入验证
            if config['start'] == config['stop']:
                raise ValueError("起始值和终止值不能相同")
            if sweep_type == "线性" and config['step'] < 2:
                raise ValueError("线性扫描步数必须≥2")
            if sweep_type == "对数" and config['points'] < 2:
                raise ValueError("对数扫描点数必须≥2")

            # 创建并启动扫描线程
            self.scan_thread = ScanningThread(self.keithley, config, source_mode)
            self.scan_thread.error.connect(lambda e: QMessageBox.critical(self, "错误", e))
            self.scan_thread.finished.connect(self.handle_scan_completion)
            self.scan_thread.start()

            QMessageBox.information(self, "扫描启动", "扫描已开始，请等待完成...")

        except ValueError as ve:
            QMessageBox.critical(self, "输入错误", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动扫描失败: {str(e)}")

    def handle_scan_completion(self):
        """处理扫描正常完成"""
        QMessageBox.information(self, "扫描完成", "扫描操作已成功结束！")
        # 安全清理线程
        if self.scan_thread is not None:
            if self.scan_thread.isRunning():
                self.scan_thread.stop()  # 设置停止标志
                self.scan_thread.quit()  # 退出事件循环
                self.scan_thread.wait(1000)  # 等待线程结束
            self.scan_thread = None
        # print("扫描完成", "扫描操作已成功结束！")

    def handle_scan_error(self, error_msg):
        """处理扫描错误"""
        QMessageBox.critical(self, "扫描中断", f"发生错误:\n{error_msg}")
        # 强制终止线程
        if self.scanning_thread is not None:
            if self.scanning_thread.isRunning():
                self.scanning_thread.stop()  # 设置停止标志
                self.scanning_thread.quit()  # 退出事件循环
                self.scanning_thread.wait(1000)  # 等待线程结束
            self.scanning_thread = None

################################################################# 2430扫描模式函数 ##################################################################
    def init2430_scanning_mode(self):
        """初始化扫描模式控件"""
        # # 替换扫描结果组件
        self.sweep2430Result = SweepWidget2430()
        layout_preview = QVBoxLayout(self.w_2430sweepResultWidget)
        layout_preview.addWidget(self.sweep2430Result)
        # 设置默认值
        self.w_2430SweepStartInput.setPlainText("0")
        self.w_2430SweepEndInput.setPlainText("10")  # 终止值
        self.w_2430SweepStepInput.setPlainText("1")  # 步数
        self.w_2430SweepIVProtectionInput.setPlainText("10")  # 电压保护
        self.w_2430SweepDelayInput.setPlainText("1")  # 测量延时
        # 设置单位默认值
        self.w_2430chooseSizeOfStartInput.setCurrentIndex(1)  # 起始单位
        self.w_2430chooseSizeOfEndInput.setCurrentIndex(1)  # 终止单位
        self.w_2430chooseSizeOfStepInput.setCurrentIndex(1)  # 终止单位
        self.w_2430chooseSizeOfSweepIVProtection.setCurrentIndex(0)  # 电压保护单位
        self.w_2430chooseSizeOfSweepDelay.setCurrentIndex(0)  # 测量延时单位
        # 设置模式默认值
        self.w_2430chooseSourceOfSweep.setCurrentIndex(0)  # 电流扫描
        self.w_2430chooseTypeOfSweep.setCurrentIndex(0)  # 线性扫描
        # 设置输输入框为单行模式
        self.w_2430SweepStartInput.setMaximumHeight(30)
        self.w_2430SweepStartInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430SweepStartInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430SweepStartInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_2430SweepEndInput.setMaximumHeight(30)
        self.w_2430SweepEndInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430SweepEndInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430SweepEndInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_2430SweepStepInput.setMaximumHeight(30)
        self.w_2430SweepStepInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430SweepStepInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430SweepStepInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_2430SweepIVProtectionInput.setMaximumHeight(30)
        self.w_2430SweepIVProtectionInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430SweepIVProtectionInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430SweepIVProtectionInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.w_2430SweepDelayInput.setMaximumHeight(30)
        self.w_2430SweepDelayInput.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430SweepDelayInput.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.w_2430SweepDelayInput.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        # 调整输入框字体大小和边距
        self.w_2430SweepStartInput.setStyleSheet("""
                                    QTextEdit {
                                        padding: 0px;     /* 减少内边距 */
                                        margin: 0px;      /* 减少外边距 */
                                    }
                                """)
        self.w_2430SweepEndInput.setStyleSheet("""
                                            QTextEdit {
                                                padding: 0px;     /* 减少内边距 */
                                                margin: 0px;      /* 减少外边距 */
                                            }
                                        """)
        self.w_2430SweepStepInput.setStyleSheet("""
                                                    QTextEdit {
                                                        padding: 0px;     /* 减少内边距 */
                                                        margin: 0px;      /* 减少外边距 */
                                                    }
                                                """)
        self.w_2430SweepIVProtectionInput.setStyleSheet("""
                                                            QTextEdit {
                                                                padding: 0px;     /* 减少内边距 */
                                                                margin: 0px;      /* 减少外边距 */
                                                            }
                                                        """)
        self.w_2430SweepDelayInput.setStyleSheet("""
                                                                    QTextEdit {
                                                                        padding: 0px;     /* 减少内边距 */
                                                                        margin: 0px;      /* 减少外边距 */
                                                                    }
                                                                """)
        # 连接信号
        self.w_2430ConfirmSweepModeSettings.clicked.connect(self.start2430_scanning)
        self.w_2430chooseSourceOfSweep.currentIndexChanged.connect(self.toggle2430_sweep_mode)
        self.w_2430chooseTypeOfSweep.currentIndexChanged.connect(self.toggle2430_source_mode)
        # 初始化标签显示
        self.toggle2430_source_mode(0)  # 默认电流源
        self.toggle2430_sweep_mode(0)  # 默认线性扫描
        # 初始化扫描线程
        self.scan2430_thread = None
        self.scanning = False

    def toggle2430_source_mode(self, index):         # 切换线性/对数扫描模式文字标注
        if index == 0:  # 线性扫描
            self.w_label_SweepStepPoint_2.setText("步长:")
            self.w_2430SweepStepInput.setPlaceholderText("1")
            self.w_2430chooseSizeOfStepInput.setCurrentIndex(1)
        else:  # 对数扫描
            self.w_label_SweepStepPoint_2.setText("点数(≥2):")
            self.w_2430SweepStepInput.setPlaceholderText("10")
            self.w_2430chooseSizeOfStepInput.setCurrentIndex(0)

    def toggle2430_sweep_mode(self, index):
        """切换源模式时更新单位标签"""
        # 0-电流源 1-电压源
        if index == 0:
            self.w_label_seconds_14.setText("A")
            self.w_label_seconds_13.setText("A")
            self.w_label_seconds_12.setText("V")
            self.w_label_seconds_15.setText("A")
            self.w_label_IVProtection_2.setText("电压保护：")
        else:
            self.w_label_seconds_14.setText("V")
            self.w_label_seconds_13.setText("V")
            self.w_label_seconds_12.setText("A")
            self.w_label_seconds_15.setText("V")
            self.w_label_IVProtection_2.setText("电流保护：")

    def start2430_scanning(self):
        try:
            # 获取扫描参数
            source_mode = self.w_2430chooseSourceOfSweep.currentIndex()  # 0-电流源 1-电压源
            sweep_type = 'linear' if self.w_2430chooseTypeOfSweep.currentIndex() == 0 else 'log'

            # 单位转换函数
            def get_unit_value(text_edit, combo_box):
                value = float(text_edit.toPlainText())
                unit = combo_box.currentText()
                multiplier = {
                    'n': 1e-9,
                    'u': 1e-6,
                    'm': 1e-3,
                    '': 1
                }.get(unit, 1)
                return value * multiplier

            # 参数收集
            config = {
                'sweep_type': sweep_type,
                'start': get_unit_value(self.w_2430SweepStartInput, self.w_2430chooseSizeOfStartInput),
                'stop': get_unit_value(self.w_2430SweepEndInput, self.w_2430chooseSizeOfEndInput),
                'step': get_unit_value(self.w_2430SweepStepInput, self.w_2430chooseSizeOfStepInput),
                'points': int(self.w_2430SweepStepInput.toPlainText()),
                'protection': get_unit_value(self.w_2430SweepIVProtectionInput, self.w_2430chooseSizeOfSweepIVProtection),
                'delay': get_unit_value(self.w_2430SweepDelayInput, self.w_2430chooseSizeOfSweepDelay)
            }

            print(config)

            # 输入验证
            # if config['start'] == config['stop']:
            #     raise ValueError("起始值和终止值不能相同")
            # if sweep_type == "线性" and config['step'] < 2:
            #     raise ValueError("线性扫描步数必须≥2")
            # if sweep_type == "对数" and config['points'] < 2:
            #     raise ValueError("对数扫描点数必须≥2")

            # 创建并启动扫描线程
            self.scan2430_thread = Scanning2430Thread(self.keithley2430, config, source_mode)
            self.scan2430_thread.error.connect(lambda e: QMessageBox.critical(self, "错误", e))
            self.scan2430_thread.finished.connect(self.handle2430_scan_completion)
            self.scan2430_thread.start()

            QMessageBox.information(self, "扫描启动", "扫描已开始，请等待完成...")

        except ValueError as ve:
            QMessageBox.critical(self, "输入错误", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动扫描失败: {str(e)}")


    def handle2430_scan_completion(self):
        """处理扫描正常完成"""
        QMessageBox.information(self, "扫描完成", "扫描操作已成功结束！")
        # 安全清理线程
        if self.scan2430_thread is not None:
            if self.scan2430_thread.isRunning():
                self.scan2430_thread.stop()  # 设置停止标志
                self.scan2430_thread.quit()  # 退出事件循环
                self.scan2430_thread.wait(1000)  # 等待线程结束
            self.scan2430_thread = None
        # print("扫描完成", "扫描操作已成功结束！")


####################################################### 信号发生器相关代码 ####################################################

    def Generator_UI_init(self):
        # 连接按钮和函数
        self.pushButton_ch1_ON.clicked.connect(self.ch1_ON)
        self.pushButton_ch1_OFF.clicked.connect(self.ch1_OFF)
        self.pushButton_ch2_ON.clicked.connect(self.ch2_ON)
        self.pushButton_ch2_OFF.clicked.connect(self.ch2_OFF)

        self.pushButton_ch1_setPara.clicked.connect(self.set_para)
        self.comboBox_ch1_mode_mode.currentIndexChanged.connect(self.ch1_mode_combo_changed)
        self.comboBox_ch2_mode_mode.currentIndexChanged.connect(self.ch2_mode_combo_changed)

        # 设置默认值
        # 输出波形默认方波
        self.tabWidget_ch1_wave.setCurrentIndex(1)
        self.tabWidget_ch2_wave.setCurrentIndex(1)
        # 频率默认kHz，周期默认ms
        self.comboBox_ch1_sine_freq_freq_unit.setCurrentIndex(1)
        self.comboBox_ch1_sine_freq_cycle_unit.setCurrentIndex(1)
        self.comboBox_ch1_square_freq_freq_unit.setCurrentIndex(1)
        self.comboBox_ch1_square_freq_cycle_unit.setCurrentIndex(1)
        self.comboBox_ch1_PWM_freq_freq_unit.setCurrentIndex(1)
        self.comboBox_ch1_PWM_freq_cycle_unit.setCurrentIndex(1)
        # 电压默认V
        self.comboBox_ch1_sine_vol_hlvol_hunit.setCurrentIndex(1)
        self.comboBox_ch1_sine_vol_hlvol_lunit.setCurrentIndex(1)
        self.comboBox_ch1_sine_vol_appoff_appunit.setCurrentIndex(1)
        self.comboBox_ch1_sine_vol_appoff_offunit.setCurrentIndex(1)
        self.comboBox_ch1_square_vol_hlvol_hunit.setCurrentIndex(1)
        self.comboBox_ch1_square_vol_hlvol_lunit.setCurrentIndex(1)
        self.comboBox_ch1_square_vol_appoff_appunit.setCurrentIndex(1)
        self.comboBox_ch1_square_vol_appoff_offunit.setCurrentIndex(1)
        self.comboBox_ch1_PWM_vol_hlvol_hunit.setCurrentIndex(1)
        self.comboBox_ch1_PWM_vol_hlvol_lunit.setCurrentIndex(1)
        self.comboBox_ch1_PWM_vol_appoff_appunit.setCurrentIndex(1)
        self.comboBox_ch1_PWM_vol_appoff_offunit.setCurrentIndex(1)

        # ch2设置方法默认频率、高-低电平
        self.tabWidget_ch2_wave.setCurrentIndex(1)
        self.tabWidget_ch2_wave.setCurrentIndex(1)
        # 频率默认kHz，周期默认ms
        self.comboBox_ch2_sine_freq_freq_unit.setCurrentIndex(1)
        self.comboBox_ch2_sine_freq_cycle_unit.setCurrentIndex(1)
        self.comboBox_ch2_square_freq_freq_unit.setCurrentIndex(1)
        self.comboBox_ch2_square_freq_cycle_unit.setCurrentIndex(1)
        self.comboBox_ch2_PWM_freq_freq_unit.setCurrentIndex(1)
        self.comboBox_ch2_PWM_freq_cycle_unit.setCurrentIndex(1)
        # 电压默认V
        self.comboBox_ch2_sine_vol_hlvol_hunit.setCurrentIndex(1)
        self.comboBox_ch2_sine_vol_hlvol_lunit.setCurrentIndex(1)
        self.comboBox_ch2_sine_vol_appoff_appunit.setCurrentIndex(1)
        self.comboBox_ch2_sine_vol_appoff_offunit.setCurrentIndex(1)
        self.comboBox_ch2_square_vol_hlvol_hunit.setCurrentIndex(1)
        self.comboBox_ch2_square_vol_hlvol_lunit.setCurrentIndex(1)
        self.comboBox_ch2_square_vol_appoff_appunit.setCurrentIndex(1)
        self.comboBox_ch2_square_vol_appoff_offunit.setCurrentIndex(1)
        self.comboBox_ch2_PWM_vol_hlvol_hunit.setCurrentIndex(1)
        self.comboBox_ch2_PWM_vol_hlvol_lunit.setCurrentIndex(1)
        self.comboBox_ch2_PWM_vol_appoff_appunit.setCurrentIndex(1)
        self.comboBox_ch2_PWM_vol_appoff_offunit.setCurrentIndex(1)

        # 隐藏burst选项
        self.frame_ch2_mode_burst.setVisible(False)
        self.frame_ch1_mode_burst.setVisible(False)

    # 连接按钮的函数

    def show_saveload_dialog(self):
        dialog_saveload = Dialog_saveload(parent=self)  # 指定父对象
        dialog_saveload.setWindowTitle("保存/加载")  # 修改窗口标题
        dialog_saveload.exec()

    def show_about_dialog(self):
        dialog_about = Dialog_about(parent=self)  # 指定父对象
        dialog_about.setWindowTitle("关于&帮助")  # 修改窗口标题
        dialog_about.exec()

    def ch1_ON(self):  # 开启/关闭ch1输出
        self.AFG1.output_on(1)

    def ch1_OFF(self):
        self.AFG1.output_off(1)

    def ch2_ON(self):  # 开启/关闭ch2输出
        self.AFG1.output_on(2)
    def ch2_OFF(self):
        self.AFG1.output_off(2)

    def ch1_mode_combo_changed(self):
        if (self.comboBox_ch1_mode_mode.currentIndex() == 0):
            self.frame_ch1_mode_burst.setVisible(False)  # 隐藏frame
        elif (self.comboBox_ch1_mode_mode.currentIndex() == 1):
            self.frame_ch1_mode_burst.setVisible(True)  # 显示frame

    def ch2_mode_combo_changed(self):
        if (self.comboBox_ch2_mode_mode.currentIndex() == 0):
            self.frame_ch2_mode_burst.setVisible(False)  # 隐藏frame
        elif (self.comboBox_ch2_mode_mode.currentIndex() == 1):
            self.frame_ch2_mode_burst.setVisible(True)  # 显示frame

    def set_para(self):  
        try:
            # 设置ch1参数
            # 读取负载阻抗
            ch1_mode_inpedance_para = self.doubleSpinBox_ch1_mode_inpedance_para.value()
            ch1_mode_inpedance_unit = self.comboBox_ch1_mode_inpedance_unit.currentText()
            ch1_mode_inpedance_unit_multiplier = {
                'Ω': 1,  # Ω
                'kΩ': 1e3,  # kΩ → Ω
            }.get(ch1_mode_inpedance_unit, 1)  # 默认为Ω，无需转换
            # ================================================选中正弦波======================================================
            if (self.tabWidget_ch1_wave.currentIndex() == 0):  # 选中正弦波
                if (self.tabWidget_ch1_sine_freq.currentIndex() == 0):  # 选中频率
                    # 读取频率
                    ch1_sine_freq_freq_value = self.doublespinBox_ch1_sine_freq_freq_para.value()
                    ch1_sine_freq_freq_unit = self.comboBox_ch1_sine_freq_freq_unit.currentText()
                    ch1_sine_freq_freq_unit_multiplier = {
                        'Hz': 1,  # Hz
                        'kHz': 1e3,  # kHz → Hz
                        'MHz': 1e6,  # MHz → Hz
                    }.get(ch1_sine_freq_freq_unit, 1)  # 默认为Hz，无需转换
                    # 计算频率：数值*单位
                    ch1_sine_freq_freq_value_out = ch1_sine_freq_freq_value * ch1_sine_freq_freq_unit_multiplier
                elif (self.tabWidget_ch1_sine_freq.currentIndex() == 1):  # 选中周期
                    # 读取周期
                    ch1_sine_freq_cycle_value = self.doublespinBox_ch1_sine_freq_cycle_para.value()
                    ch1_sine_freq_cycle_unit = self.comboBox_ch1_sine_freq_cycle_unit.currentText()
                    ch1_sine_freq_cycle_unit_multiplier = {
                        's': 1,  # s
                        'ms': 1e-3,  # ms → s
                        'μs': 1e-6,  # μs → s
                        'ns': 1e-9,  # ns → s
                    }.get(ch1_sine_freq_cycle_unit, 1)  # 默认为s，无需转换
                    # 计算周期：数值*单位, 周期 → 频率
                    ch1_sine_freq_freq_value_out = 1 / (ch1_sine_freq_cycle_value * ch1_sine_freq_cycle_unit_multiplier)

                if (self.tabWidget_ch1_sine_vol.currentIndex() == 0):  # 选中高-低电平
                    # 读取高电平
                    ch1_sine_vol_hlvol_hpara = self.doubleSpinBox_ch1_sine_vol_hlvol_hpara.value()
                    ch1_sine_vol_hlvol_hunit = self.comboBox_ch1_sine_vol_hlvol_hunit.currentText()
                    ch1_sine_vol_hlvol_hunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch1_sine_vol_hlvol_hunit, 1)  # 默认为V，无需转换
                    # 读取低电平
                    ch1_sine_vol_hlvol_lpara = self.doubleSpinBox_ch1_sine_vol_hlvol_lpara.value()
                    ch1_sine_vol_hlvol_lunit = self.comboBox_ch1_sine_vol_hlvol_lunit.currentText()
                    ch1_sine_vol_hlvol_lunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch1_sine_vol_hlvol_lunit, 1)  # 默认为V，无需转换

                    # 计算电平：数值*单位
                    ch1_sine_vol_hlvol_hout = ch1_sine_vol_hlvol_hpara * ch1_sine_vol_hlvol_hunit_multiplier
                    ch1_sine_vol_hlvol_lout = ch1_sine_vol_hlvol_lpara * ch1_sine_vol_hlvol_lunit_multiplier

                elif (self.tabWidget_ch1_sine_vol.currentIndex() == 1):  # 选中幅度-偏置
                    # 读取幅度
                    ch1_sine_vol_appoff_appvalue = self.doubleSpinBox_ch1_sine_vol_appoff_apppara.value()
                    ch1_sine_vol_appoff_appunit = self.comboBox_ch1_sine_vol_appoff_appunit.currentText()
                    ch1_sine_vol_appoff_appunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch1_sine_vol_appoff_appunit, 1)  # 默认为V，无需转换
                    # 读取偏置
                    ch1_sine_vol_appoff_offvalue = self.doubleSpinBox_ch1_sine_vol_appoff_offpara.value()
                    ch1_sine_vol_appoff_offunit = self.comboBox_ch1_sine_vol_appoff_offunit.currentText()
                    ch1_sine_vol_appoff_offunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch1_sine_vol_appoff_offunit, 1)  # 默认为V，无需转换

                    # 计算电平：数值*单位, 高-低电平 → 幅度-偏置
                    ch1_sine_vol_hlvol_hout = ch1_sine_vol_appoff_offvalue * ch1_sine_vol_appoff_offunit_multiplier + 0.5 * ch1_sine_vol_appoff_appvalue * ch1_sine_vol_appoff_appunit_multiplier
                    ch1_sine_vol_hlvol_lout = ch1_sine_vol_appoff_offvalue * ch1_sine_vol_appoff_offunit_multiplier - 0.5 * ch1_sine_vol_appoff_appvalue * ch1_sine_vol_appoff_appunit_multiplier

                # 设置正弦波形
                self.AFG1.setwave_sine(1, ch1_sine_vol_hlvol_hout, ch1_sine_vol_hlvol_lout, ch1_sine_freq_freq_value_out)

            # ================================================选中方波======================================================
            elif (self.tabWidget_ch1_wave.currentIndex() == 1):  # 选中方波
                if (self.tabWidget_ch1_square_freq.currentIndex() == 0):  # 选中频率
                    # 读取频率
                    ch1_square_freq_freq_value = self.doublespinBox_ch1_square_freq_freq_para.value()
                    ch1_square_freq_freq_unit = self.comboBox_ch1_square_freq_freq_unit.currentText()
                    ch1_square_freq_freq_unit_multiplier = {
                        'Hz': 1,  # Hz
                        'kHz': 1e3,  # kHz → Hz
                        'MHz': 1e6,  # MHz → Hz
                    }.get(ch1_square_freq_freq_unit, 1)  # 默认为Hz，无需转换
                    # 计算频率：数值*单位
                    ch1_square_freq_freq_value_out = ch1_square_freq_freq_value * ch1_square_freq_freq_unit_multiplier
                elif (self.tabWidget_ch1_square_freq.currentIndex() == 1):  # 选中周期
                    # 读取周期
                    ch1_square_freq_cycle_value = self.doublespinBox_ch1_square_freq_cycle_para.value()
                    ch1_square_freq_cycle_unit = self.comboBox_ch1_square_freq_cycle_unit.currentText()
                    ch1_square_freq_cycle_unit_multiplier = {
                        's': 1,  # s
                        'ms': 1e-3,  # ms → s
                        'μs': 1e-6,  # μs → s
                        'ns': 1e-9,  # ns → s
                    }.get(ch1_square_freq_cycle_unit, 1)  # 默认为s，无需转换
                    # 计算周期：数值*单位, 周期 → 频率
                    ch1_square_freq_freq_value_out = 1 / (
                                ch1_square_freq_cycle_value * ch1_square_freq_cycle_unit_multiplier)

                if (self.tabWidget_ch1_square_vol.currentIndex() == 0):  # 选中高-低电平
                    # 读取高电平
                    ch1_square_vol_hlvol_hpara = self.doubleSpinBox_ch1_square_vol_hlvol_hpara.value()
                    ch1_square_vol_hlvol_hunit = self.comboBox_ch1_square_vol_hlvol_hunit.currentText()
                    ch1_square_vol_hlvol_hunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch1_square_vol_hlvol_hunit, 1)  # 默认为V，无需转换
                    # 读取低电平
                    ch1_square_vol_hlvol_lpara = self.doubleSpinBox_ch1_square_vol_hlvol_lpara.value()
                    ch1_square_vol_hlvol_lunit = self.comboBox_ch1_square_vol_hlvol_lunit.currentText()
                    ch1_square_vol_hlvol_lunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch1_square_vol_hlvol_lunit, 1)  # 默认为V，无需转换

                    # 计算电平：数值*单位
                    ch1_square_vol_hlvol_hout = ch1_square_vol_hlvol_hpara * ch1_square_vol_hlvol_hunit_multiplier
                    ch1_square_vol_hlvol_lout = ch1_square_vol_hlvol_lpara * ch1_square_vol_hlvol_lunit_multiplier

                elif (self.tabWidget_ch1_square_vol.currentIndex() == 1):  # 选中幅度-偏置
                    # 读取幅度
                    ch1_square_vol_appoff_appvalue = self.doubleSpinBox_ch1_square_vol_appoff_apppara.value()
                    ch1_square_vol_appoff_appunit = self.comboBox_ch1_square_vol_appoff_appunit.currentText()
                    ch1_square_vol_appoff_appunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch1_square_vol_appoff_appunit, 1)  # 默认为V，无需转换
                    # 读取偏置
                    ch1_square_vol_appoff_offvalue = self.doubleSpinBox_ch1_square_vol_appoff_offpara.value()
                    ch1_square_vol_appoff_offunit = self.comboBox_ch1_square_vol_appoff_offunit.currentText()
                    ch1_square_vol_appoff_offunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch1_square_vol_appoff_offunit, 1)  # 默认为V，无需转换

                    # 计算电平：数值*单位, 高-低电平 → 幅度-偏置
                    ch1_square_vol_hlvol_hout = ch1_square_vol_appoff_offvalue * ch1_square_vol_appoff_offunit_multiplier + 0.5 * ch1_square_vol_appoff_appvalue * ch1_square_vol_appoff_appunit_multiplier
                    ch1_square_vol_hlvol_lout = ch1_square_vol_appoff_offvalue * ch1_square_vol_appoff_offunit_multiplier - 0.5 * ch1_square_vol_appoff_appvalue * ch1_square_vol_appoff_appunit_multiplier

                # 设置方波形
                self.AFG1.setwave_square(1, ch1_square_vol_hlvol_hout, ch1_square_vol_hlvol_lout,
                                    ch1_square_freq_freq_value_out)

            # ================================================选中PWM波======================================================
            elif (self.tabWidget_ch1_wave.currentIndex() == 2):  # 选中PWM波
                if (self.tabWidget_ch1_PWM_freq.currentIndex() == 0):  # 选中频率
                    # 读取频率
                    ch1_PWM_freq_freq_value = self.doublespinBox_ch1_PWM_freq_freq_para.value()
                    ch1_PWM_freq_freq_unit = self.comboBox_ch1_PWM_freq_freq_unit.currentText()
                    ch1_PWM_freq_freq_unit_multiplier = {
                        'Hz': 1,  # Hz
                        'kHz': 1e3,  # kHz → Hz
                        'MHz': 1e6,  # MHz → Hz
                    }.get(ch1_PWM_freq_freq_unit, 1)  # 默认为Hz，无需转换
                    # 计算频率：数值*单位
                    ch1_PWM_freq_freq_value_out = ch1_PWM_freq_freq_value * ch1_PWM_freq_freq_unit_multiplier
                elif (self.tabWidget_ch1_PWM_freq.currentIndex() == 1):  # 选中周期
                    # 读取周期
                    ch1_PWM_freq_cycle_value = self.doublespinBox_ch1_PWM_freq_cycle_para.value()
                    ch1_PWM_freq_cycle_unit = self.comboBox_ch1_PWM_freq_cycle_unit.currentText()
                    ch1_PWM_freq_cycle_unit_multiplier = {
                        's': 1,  # s
                        'ms': 1e-3,  # ms → s
                        'μs': 1e-6,  # μs → s
                        'ns': 1e-9,  # ns → s
                    }.get(ch1_PWM_freq_cycle_unit, 1)  # 默认为s，无需转换
                    # 计算周期：数值*单位, 周期 → 频率
                    ch1_PWM_freq_freq_value_out = 1 / (ch1_PWM_freq_cycle_value * ch1_PWM_freq_cycle_unit_multiplier)

                if (self.tabWidget_ch1_PWM_vol.currentIndex() == 0):  # 选中高-低电平
                    # 读取高电平
                    ch1_PWM_vol_hlvol_hpara = self.doubleSpinBox_ch1_PWM_vol_hlvol_hpara.value()
                    ch1_PWM_vol_hlvol_hunit = self.comboBox_ch1_PWM_vol_hlvol_hunit.currentText()
                    ch1_PWM_vol_hlvol_hunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch1_PWM_vol_hlvol_hunit, 1)  # 默认为V，无需转换
                    # 读取低电平
                    ch1_PWM_vol_hlvol_lpara = self.doubleSpinBox_ch1_PWM_vol_hlvol_lpara.value()
                    ch1_PWM_vol_hlvol_lunit = self.comboBox_ch1_PWM_vol_hlvol_lunit.currentText()
                    ch1_PWM_vol_hlvol_lunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch1_PWM_vol_hlvol_lunit, 1)  # 默认为V，无需转换

                    # 计算电平：数值*单位
                    ch1_PWM_vol_hlvol_hout = ch1_PWM_vol_hlvol_hpara * ch1_PWM_vol_hlvol_hunit_multiplier
                    ch1_PWM_vol_hlvol_lout = ch1_PWM_vol_hlvol_lpara * ch1_PWM_vol_hlvol_lunit_multiplier

                elif (self.tabWidget_ch1_PWM_vol.currentIndex() == 1):  # 选中幅度-偏置
                    # 读取幅度
                    ch1_PWM_vol_appoff_appvalue = self.doubleSpinBox_ch1_PWM_vol_appoff_apppara.value()
                    ch1_PWM_vol_appoff_appunit = self.comboBox_ch1_PWM_vol_appoff_appunit.currentText()
                    ch1_PWM_vol_appoff_appunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch1_PWM_vol_appoff_appunit, 1)  # 默认为V，无需转换
                    # 读取偏置
                    ch1_PWM_vol_appoff_offvalue = self.doubleSpinBox_ch1_PWM_vol_appoff_offpara.value()
                    ch1_PWM_vol_appoff_offunit = self.comboBox_ch1_PWM_vol_appoff_offunit.currentText()
                    ch1_PWM_vol_appoff_offunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch1_PWM_vol_appoff_offunit, 1)  # 默认为V，无需转换

                    # 计算电平：数值*单位, 高-低电平 → 幅度-偏置
                    ch1_PWM_vol_hlvol_hout = ch1_PWM_vol_appoff_offvalue * ch1_PWM_vol_appoff_offunit_multiplier + 0.5 * ch1_PWM_vol_appoff_appvalue * ch1_PWM_vol_appoff_appunit_multiplier
                    ch1_PWM_vol_hlvol_lout = ch1_PWM_vol_appoff_offvalue * ch1_PWM_vol_appoff_offunit_multiplier - 0.5 * ch1_PWM_vol_appoff_appvalue * ch1_PWM_vol_appoff_appunit_multiplier

                # 读取占空比
                ch1_PWM_duty = self.doubleSpinBox_ch1_PWM_duty.value()

                # 设置PWM波形
                self.AFG1.setwave_PWM(1, ch1_PWM_vol_hlvol_hout, ch1_PWM_vol_hlvol_lout, ch1_PWM_freq_freq_value_out,
                                 ch1_PWM_duty)

            else:
                QMessageBox.information(self, "error", "error")

            # 发送指令，在仪器上设置上述读取的参数
            # 设置反相
            if (self.checkBox_ch1_reverse.isChecked()):
                self.AFG1.set_reverse(1, 1)
            else:
                self.AFG1.set_reverse(1, 0)

            # 设置负载阻抗
            if (ch1_mode_inpedance_unit == '高阻抗'):
                self.AFG1.set_impedance_highZ(1)
            else:
                self.AFG1.set_impedance(1, ch1_mode_inpedance_para * ch1_mode_inpedance_unit_multiplier)



            # 设置ch2参数
            # 读取负载阻抗
            ch2_mode_inpedance_para = self.doubleSpinBox_ch2_mode_inpedance_para.value()
            ch2_mode_inpedance_unit = self.comboBox_ch2_mode_inpedance_unit.currentText()
            ch2_mode_inpedance_unit_multiplier = {
                'Ω': 1,  # Ω
                'kΩ': 1e3,  # kΩ → Ω
            }.get(ch2_mode_inpedance_unit, 1)  # 默认为Ω，无需转换
            # ================================================选中正弦波======================================================
            if (self.tabWidget_ch2_wave.currentIndex() == 0):  # 选中正弦波
                if (self.tabWidget_ch2_sine_freq.currentIndex() == 0):  # 选中频率
                    # 读取频率
                    ch2_sine_freq_freq_value = self.doublespinBox_ch2_sine_freq_freq_para.value()
                    ch2_sine_freq_freq_unit = self.comboBox_ch2_sine_freq_freq_unit.currentText()
                    ch2_sine_freq_freq_unit_multiplier = {
                        'Hz': 1,  # Hz
                        'kHz': 1e3,  # kHz → Hz
                        'MHz': 1e6,  # MHz → Hz
                    }.get(ch2_sine_freq_freq_unit, 1)  # 默认为Hz，无需转换
                    # 计算频率：数值*单位
                    ch2_sine_freq_freq_value_out = ch2_sine_freq_freq_value * ch2_sine_freq_freq_unit_multiplier
                elif (self.tabWidget_ch2_sine_freq.currentIndex() == 1):  # 选中周期
                    # 读取周期
                    ch2_sine_freq_cycle_value = self.doublespinBox_ch2_sine_freq_cycle_para.value()
                    ch2_sine_freq_cycle_unit = self.comboBox_ch2_sine_freq_cycle_unit.currentText()
                    ch2_sine_freq_cycle_unit_multiplier = {
                        's': 1,  # s
                        'ms': 1e-3,  # ms → s
                        'μs': 1e-6,  # μs → s
                        'ns': 1e-9,  # ns → s
                    }.get(ch2_sine_freq_cycle_unit, 1)  # 默认为s，无需转换
                    # 计算周期：数值*单位, 周期 → 频率
                    ch2_sine_freq_freq_value_out = 1 / (ch2_sine_freq_cycle_value * ch2_sine_freq_cycle_unit_multiplier)

                if (self.tabWidget_ch2_sine_vol.currentIndex() == 0):  # 选中高-低电平
                    # 读取高电平
                    ch2_sine_vol_hlvol_hpara = self.doubleSpinBox_ch2_sine_vol_hlvol_hpara.value()
                    ch2_sine_vol_hlvol_hunit = self.comboBox_ch2_sine_vol_hlvol_hunit.currentText()
                    ch2_sine_vol_hlvol_hunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch2_sine_vol_hlvol_hunit, 1)  # 默认为V，无需转换
                    # 读取低电平
                    ch2_sine_vol_hlvol_lpara = self.doubleSpinBox_ch2_sine_vol_hlvol_lpara.value()
                    ch2_sine_vol_hlvol_lunit = self.comboBox_ch2_sine_vol_hlvol_lunit.currentText()
                    ch2_sine_vol_hlvol_lunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch2_sine_vol_hlvol_lunit, 1)  # 默认为V，无需转换

                    # 计算电平：数值*单位
                    ch2_sine_vol_hlvol_hout = ch2_sine_vol_hlvol_hpara * ch2_sine_vol_hlvol_hunit_multiplier
                    ch2_sine_vol_hlvol_lout = ch2_sine_vol_hlvol_lpara * ch2_sine_vol_hlvol_lunit_multiplier

                elif (self.tabWidget_ch2_sine_vol.currentIndex() == 1):  # 选中幅度-偏置
                    # 读取幅度
                    ch2_sine_vol_appoff_appvalue = self.doubleSpinBox_ch2_sine_vol_appoff_apppara.value()
                    ch2_sine_vol_appoff_appunit = self.comboBox_ch2_sine_vol_appoff_appunit.currentText()
                    ch2_sine_vol_appoff_appunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch2_sine_vol_appoff_appunit, 1)  # 默认为V，无需转换
                    # 读取偏置
                    ch2_sine_vol_appoff_offvalue = self.doubleSpinBox_ch2_sine_vol_appoff_offpara.value()
                    ch2_sine_vol_appoff_offunit = self.comboBox_ch2_sine_vol_appoff_offunit.currentText()
                    ch2_sine_vol_appoff_offunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch2_sine_vol_appoff_offunit, 1)  # 默认为V，无需转换

                    # 计算电平：数值*单位, 高-低电平 → 幅度-偏置
                    ch2_sine_vol_hlvol_hout = ch2_sine_vol_appoff_offvalue * ch2_sine_vol_appoff_offunit_multiplier + 0.5 * ch2_sine_vol_appoff_appvalue * ch2_sine_vol_appoff_appunit_multiplier
                    ch2_sine_vol_hlvol_lout = ch2_sine_vol_appoff_offvalue * ch2_sine_vol_appoff_offunit_multiplier - 0.5 * ch2_sine_vol_appoff_appvalue * ch2_sine_vol_appoff_appunit_multiplier

                # 设置正弦波形
                self.AFG1.setwave_sine(2, ch2_sine_vol_hlvol_hout, ch2_sine_vol_hlvol_lout,
                                       ch2_sine_freq_freq_value_out)

            # ================================================选中方波======================================================
            elif (self.tabWidget_ch2_wave.currentIndex() == 1):  # 选中方波
                if (self.tabWidget_ch2_square_freq.currentIndex() == 0):  # 选中频率
                    # 读取频率
                    ch2_square_freq_freq_value = self.doublespinBox_ch2_square_freq_freq_para.value()
                    ch2_square_freq_freq_unit = self.comboBox_ch2_square_freq_freq_unit.currentText()
                    ch2_square_freq_freq_unit_multiplier = {
                        'Hz': 1,  # Hz
                        'kHz': 1e3,  # kHz → Hz
                        'MHz': 1e6,  # MHz → Hz
                    }.get(ch2_square_freq_freq_unit, 1)  # 默认为Hz，无需转换
                    # 计算频率：数值*单位
                    ch2_square_freq_freq_value_out = ch2_square_freq_freq_value * ch2_square_freq_freq_unit_multiplier
                elif (self.tabWidget_ch2_square_freq.currentIndex() == 1):  # 选中周期
                    # 读取周期
                    ch2_square_freq_cycle_value = self.doublespinBox_ch2_square_freq_cycle_para.value()
                    ch2_square_freq_cycle_unit = self.comboBox_ch2_square_freq_cycle_unit.currentText()
                    ch2_square_freq_cycle_unit_multiplier = {
                        's': 1,  # s
                        'ms': 1e-3,  # ms → s
                        'μs': 1e-6,  # μs → s
                        'ns': 1e-9,  # ns → s
                    }.get(ch2_square_freq_cycle_unit, 1)  # 默认为s，无需转换
                    # 计算周期：数值*单位, 周期 → 频率
                    ch2_square_freq_freq_value_out = 1 / (
                            ch2_square_freq_cycle_value * ch2_square_freq_cycle_unit_multiplier)

                if (self.tabWidget_ch2_square_vol.currentIndex() == 0):  # 选中高-低电平
                    # 读取高电平
                    ch2_square_vol_hlvol_hpara = self.doubleSpinBox_ch2_square_vol_hlvol_hpara.value()
                    ch2_square_vol_hlvol_hunit = self.comboBox_ch2_square_vol_hlvol_hunit.currentText()
                    ch2_square_vol_hlvol_hunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch2_square_vol_hlvol_hunit, 1)  # 默认为V，无需转换
                    # 读取低电平
                    ch2_square_vol_hlvol_lpara = self.doubleSpinBox_ch2_square_vol_hlvol_lpara.value()
                    ch2_square_vol_hlvol_lunit = self.comboBox_ch2_square_vol_hlvol_lunit.currentText()
                    ch2_square_vol_hlvol_lunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch2_square_vol_hlvol_lunit, 1)  # 默认为V，无需转换

                    # 计算电平：数值*单位
                    ch2_square_vol_hlvol_hout = ch2_square_vol_hlvol_hpara * ch2_square_vol_hlvol_hunit_multiplier
                    ch2_square_vol_hlvol_lout = ch2_square_vol_hlvol_lpara * ch2_square_vol_hlvol_lunit_multiplier

                elif (self.tabWidget_ch2_square_vol.currentIndex() == 1):  # 选中幅度-偏置
                    # 读取幅度
                    ch2_square_vol_appoff_appvalue = self.doubleSpinBox_ch2_square_vol_appoff_apppara.value()
                    ch2_square_vol_appoff_appunit = self.comboBox_ch2_square_vol_appoff_appunit.currentText()
                    ch2_square_vol_appoff_appunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch2_square_vol_appoff_appunit, 1)  # 默认为V，无需转换
                    # 读取偏置
                    ch2_square_vol_appoff_offvalue = self.doubleSpinBox_ch2_square_vol_appoff_offpara.value()
                    ch2_square_vol_appoff_offunit = self.comboBox_ch2_square_vol_appoff_offunit.currentText()
                    ch2_square_vol_appoff_offunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch2_square_vol_appoff_offunit, 1)  # 默认为V，无需转换

                    # 计算电平：数值*单位, 高-低电平 → 幅度-偏置
                    ch2_square_vol_hlvol_hout = ch2_square_vol_appoff_offvalue * ch2_square_vol_appoff_offunit_multiplier + 0.5 * ch2_square_vol_appoff_appvalue * ch2_square_vol_appoff_appunit_multiplier
                    ch2_square_vol_hlvol_lout = ch2_square_vol_appoff_offvalue * ch2_square_vol_appoff_offunit_multiplier - 0.5 * ch2_square_vol_appoff_appvalue * ch2_square_vol_appoff_appunit_multiplier

                # 设置方波形
                self.AFG1.setwave_square(2, ch2_square_vol_hlvol_hout, ch2_square_vol_hlvol_lout,
                                         ch2_square_freq_freq_value_out)

            # ================================================选中PWM波======================================================
            elif (self.tabWidget_ch2_wave.currentIndex() == 2):  # 选中PWM波
                if (self.tabWidget_ch2_PWM_freq.currentIndex() == 0):  # 选中频率
                    # 读取频率
                    ch2_PWM_freq_freq_value = self.doublespinBox_ch2_PWM_freq_freq_para.value()
                    ch2_PWM_freq_freq_unit = self.comboBox_ch2_PWM_freq_freq_unit.currentText()
                    ch2_PWM_freq_freq_unit_multiplier = {
                        'Hz': 1,  # Hz
                        'kHz': 1e3,  # kHz → Hz
                        'MHz': 1e6,  # MHz → Hz
                    }.get(ch2_PWM_freq_freq_unit, 1)  # 默认为Hz，无需转换
                    # 计算频率：数值*单位
                    ch2_PWM_freq_freq_value_out = ch2_PWM_freq_freq_value * ch2_PWM_freq_freq_unit_multiplier
                elif (self.tabWidget_ch2_PWM_freq.currentIndex() == 1):  # 选中周期
                    # 读取周期
                    ch2_PWM_freq_cycle_value = self.doublespinBox_ch2_PWM_freq_cycle_para.value()
                    ch2_PWM_freq_cycle_unit = self.comboBox_ch2_PWM_freq_cycle_unit.currentText()
                    ch2_PWM_freq_cycle_unit_multiplier = {
                        's': 1,  # s
                        'ms': 1e-3,  # ms → s
                        'μs': 1e-6,  # μs → s
                        'ns': 1e-9,  # ns → s
                    }.get(ch2_PWM_freq_cycle_unit, 1)  # 默认为s，无需转换
                    # 计算周期：数值*单位, 周期 → 频率
                    ch2_PWM_freq_freq_value_out = 1 / (ch2_PWM_freq_cycle_value * ch2_PWM_freq_cycle_unit_multiplier)

                if (self.tabWidget_ch2_PWM_vol.currentIndex() == 0):  # 选中高-低电平
                    # 读取高电平
                    ch2_PWM_vol_hlvol_hpara = self.doubleSpinBox_ch2_PWM_vol_hlvol_hpara.value()
                    ch2_PWM_vol_hlvol_hunit = self.comboBox_ch2_PWM_vol_hlvol_hunit.currentText()
                    ch2_PWM_vol_hlvol_hunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch2_PWM_vol_hlvol_hunit, 1)  # 默认为V，无需转换
                    # 读取低电平
                    ch2_PWM_vol_hlvol_lpara = self.doubleSpinBox_ch2_PWM_vol_hlvol_lpara.value()
                    ch2_PWM_vol_hlvol_lunit = self.comboBox_ch2_PWM_vol_hlvol_lunit.currentText()
                    ch2_PWM_vol_hlvol_lunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch2_PWM_vol_hlvol_lunit, 1)  # 默认为V，无需转换

                    # 计算电平：数值*单位
                    ch2_PWM_vol_hlvol_hout = ch2_PWM_vol_hlvol_hpara * ch2_PWM_vol_hlvol_hunit_multiplier
                    ch2_PWM_vol_hlvol_lout = ch2_PWM_vol_hlvol_lpara * ch2_PWM_vol_hlvol_lunit_multiplier

                elif (self.tabWidget_ch2_PWM_vol.currentIndex() == 1):  # 选中幅度-偏置
                    # 读取幅度
                    ch2_PWM_vol_appoff_appvalue = self.doubleSpinBox_ch2_PWM_vol_appoff_apppara.value()
                    ch2_PWM_vol_appoff_appunit = self.comboBox_ch2_PWM_vol_appoff_appunit.currentText()
                    ch2_PWM_vol_appoff_appunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch2_PWM_vol_appoff_appunit, 1)  # 默认为V，无需转换
                    # 读取偏置
                    ch2_PWM_vol_appoff_offvalue = self.doubleSpinBox_ch2_PWM_vol_appoff_offpara.value()
                    ch2_PWM_vol_appoff_offunit = self.comboBox_ch2_PWM_vol_appoff_offunit.currentText()
                    ch2_PWM_vol_appoff_offunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,  # V
                    }.get(ch2_PWM_vol_appoff_offunit, 1)  # 默认为V，无需转换

                    # 计算电平：数值*单位, 高-低电平 → 幅度-偏置
                    ch2_PWM_vol_hlvol_hout = ch2_PWM_vol_appoff_offvalue * ch2_PWM_vol_appoff_offunit_multiplier + 0.5 * ch2_PWM_vol_appoff_appvalue * ch2_PWM_vol_appoff_appunit_multiplier
                    ch2_PWM_vol_hlvol_lout = ch2_PWM_vol_appoff_offvalue * ch2_PWM_vol_appoff_offunit_multiplier - 0.5 * ch2_PWM_vol_appoff_appvalue * ch2_PWM_vol_appoff_appunit_multiplier

                # 读取占空比
                ch2_PWM_duty = self.doubleSpinBox_ch2_PWM_duty.value()

                # 设置PWM波形
                self.AFG1.setwave_PWM(2, ch2_PWM_vol_hlvol_hout, ch2_PWM_vol_hlvol_lout, ch2_PWM_freq_freq_value_out,
                                      ch2_PWM_duty)

            else:
                QMessageBox.information(self, "error", "error")

            # 发送指令，在仪器上设置上述读取的参数
            # 设置反相
            if (self.checkBox_ch2_reverse.isChecked()):
                self.AFG1.set_reverse(2, 1)
            else:
                self.AFG1.set_reverse(2, 0)

            # 设置负载阻抗
            if (ch2_mode_inpedance_unit == '高阻抗'):
                self.AFG1.set_impedance_highZ(2)
            else:
                self.AFG1.set_impedance(2, ch2_mode_inpedance_para * ch2_mode_inpedance_unit_multiplier)

            QMessageBox.information(self, "成功", "信号发生器参数设置成功!")
            
            
            
            
            
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

#######################################################总体控制相关函数#####################################################

    def closeEvent(self):
        # 安全关闭2410
        try:
            if self.keithley is not None:
                # self.keithley.rampDownVoltage()
                self.keithley.outputOff()
                self.timer.stop()  # 停止2410的定时器
        except Exception as e:
            print(f"关闭2410错误: {str(e)}")
        # 安全关闭2430
        try:
            if self.keithley is not None:
                self.keithley2430_thread.stop()  # 停止线程循环
                self.keithley2430_thread.quit()  # 退出线程
                self.keithley2430_thread.wait()  # 等待线程结束
                self.keithley2430.outputOff()
        except Exception as e:
            print(f"关闭2430错误: {str(e)}")
        event.accept()

#######################################################main函数#####################################################
if __name__ == "__main__":
    # 创建应用实例
    app = QApplication(sys.argv)
    # 应用主题
    # extra = {
    #     # 字体大小设置
    #     'font_size': '10px',  # 修改为需要的字号（如 14px、18px 等）
    #     'font_family': 'TimesNewRoman',  # 可选：修改字体类型
    # }
    # apply_stylesheet(
    #     app,
    #     theme='light_teal_500.xml',
    #     extra=extra
    # )
    # 创建并显示窗口
    window = MyDialog()
    window.show()
    # 运行应用
    sys.exit(app.exec_())