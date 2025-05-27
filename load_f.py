"""""""""""""""""""""""""""""""""
Dialog_load相关函数
用于加载excel表中的一个存档

"""""""""""""""""""""""""""""""""
from PyQt5.QtWidgets import QMainWindow,QApplication,QDialog,QTableWidget, QTableWidgetItem, QScrollArea
import sys
from Auto_test_UI import Ui_Dialog  # 主界面
from saveload import Ui_Dialog_saveload  # 保存加载界面
from save import Ui_Dialog_save  # 保存加载的保存界面
from load import Ui_Dialog_load  # 保存加载的确认界面
from delt import Ui_Dialog_del  # 保存加载的删除界面
from datetime import datetime  # 获取当前时间

from qt_material import apply_stylesheet  # 界面美化库
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem
import pandas as pd

import os




class Dialog_load(QDialog, Ui_Dialog_load):
    def __init__(self, parent=None):
        super().__init__(parent)  # 设置窗口为模态（阻塞父窗口）
        self.setupUi(self)  # 初始化UI

        # 获取父窗口引用
        parent_saveload = self.parent()
        if not parent_saveload:
            QMessageBox.critical(self, "错误", "无法获取父窗口！")
            return

        # 获取当前选中的行
        selected_row = parent_saveload.tableWidget_saveload.currentRow()

        # “名称”在第2列，“备注”在第3列，根据实际Excel结构调整索引
        name_item = parent_saveload.tableWidget_saveload.item(selected_row, 1)
        remark_item = parent_saveload.tableWidget_saveload.item(selected_row, 2)

        # 设置文本内容
        if name_item:
            self.textBrowser_load_name.setText(name_item.text())
        if remark_item:
            self.textBrowser_load_remark.setText(remark_item.text())

        # 连接按钮和函数
        self.pushButton_load_cancel.clicked.connect(self.load_cancel)
        self.pushButton_load_load.clicked.connect(self.load_load)  # 按下加载


    def load_cancel(self):
        self.close()

    def load_load(self):
        try:
            # 获取父窗口（Dialog_saveload）和主窗口（MyWindow）
            saveload_dialog = self.parent()
            main_window = saveload_dialog.parent()

            # 获取列名列表
            columns = []
            for col in range(saveload_dialog.tableWidget_saveload.columnCount()):
                header = saveload_dialog.tableWidget_saveload.horizontalHeaderItem(col)
                columns.append(header.text() if header else "")

            # 遍历每一列，设置控件值
            selected_row = saveload_dialog.tableWidget_saveload.currentRow()
            for col, column_name in enumerate(columns):
                item = saveload_dialog.tableWidget_saveload.item(selected_row, col)
                if not item:
                    continue
                value = item.text().strip()

                match column_name:
                    case 'CH1\n输出模式' | 'CH2\n输出模式':
                        match value:
                            case 'Continuous': tab_value = 0
                            case 'Burst': tab_value = 1
                    case 'CH1\n波形' | 'CH2\n波形':
                        match value:
                            case '正弦波': tab_value = 0
                            case '方波': tab_value = 1
                            case 'PWM波': tab_value = 2
                    case '2410\n模式' | '2430\n模式':
                        match value:
                            case '电压源模式': tab_value = 0
                            case '电流源模式': tab_value = 1
                            case '脉冲模式': tab_value = 2
                            case '扫描模式': tab_value = 3

                match column_name:
                    case 'CH1\n输出模式': main_window.comboBox_ch1_mode_mode.setCurrentIndex(int(tab_value))
                    case 'CH1\n波形': main_window.tabWidget_ch1_wave.setCurrentIndex(int(tab_value))
                    case 'CH2\n输出模式': main_window.comboBox_ch2_mode_mode.setCurrentIndex(int(tab_value))
                    case 'CH2\n波形': main_window.tabWidget_ch2_wave.setCurrentIndex(int(tab_value))
                    case 'CH1\n正弦波\n频率值': main_window.doublespinBox_ch1_sine_freq_freq_para.setValue(float(value))
                    case 'CH1\n正弦波\n频率单位': main_window.comboBox_ch1_sine_freq_freq_unit.setCurrentText(value)
                    case 'CH1\n正弦波\n高电平值': main_window.doubleSpinBox_ch1_sine_vol_hlvol_hpara.setValue(float(value))
                    case 'CH1\n正弦波\n高电平单位': main_window.comboBox_ch1_sine_vol_hlvol_hunit.setCurrentText(value)
                    case 'CH1\n正弦波\n低电平值': main_window.doubleSpinBox_ch1_sine_vol_hlvol_lpara.setValue(float(value))
                    case 'CH1\n正弦波\n低电平单位': main_window.comboBox_ch1_sine_vol_hlvol_lunit.setCurrentText(value)

                    case 'CH1\n方波\n频率值': main_window.doublespinBox_ch1_square_freq_freq_para.setValue(float(value))
                    case 'CH1\n方波\n频率单位': main_window.comboBox_ch1_square_freq_freq_unit.setCurrentText(value)
                    case 'CH1\n方波\n高电平值': main_window.doubleSpinBox_ch1_square_vol_hlvol_hpara.setValue(float(value))
                    case 'CH1\n方波\n高电平单位': main_window.comboBox_ch1_square_vol_hlvol_hunit.setCurrentText(value)
                    case 'CH1\n方波\n低电平值': main_window.doubleSpinBox_ch1_square_vol_hlvol_lpara.setValue(float(value))
                    case 'CH1\n方波\n低电平单位': main_window.comboBox_ch1_square_vol_hlvol_lunit.setCurrentText(value)

                    case 'CH1\nPWM波\n频率值': main_window.doublespinBox_ch1_PWM_freq_freq_para.setValue(float(value))
                    case 'CH1\nPWM波\n频率单位': main_window.comboBox_ch1_PWM_freq_freq_unit.setCurrentText(value)
                    case 'CH1\nPWM波\n高电平值': main_window.doubleSpinBox_ch1_PWM_vol_hlvol_hpara.setValue(float(value))
                    case 'CH1\nPWM波\n高电平单位': main_window.comboBox_ch1_PWM_vol_hlvol_hunit.setCurrentText(value)
                    case 'CH1\nPWM波\n低电平值': main_window.doubleSpinBox_ch1_PWM_vol_hlvol_lpara.setValue(float(value))
                    case 'CH1\nPWM波\n低电平单位': main_window.comboBox_ch1_PWM_vol_hlvol_lunit.setCurrentText(value)
                    case 'CH1\nPWM波\n占空比': main_window.doubleSpinBox_ch1_PWM_duty.setValue(float(value))

                    case 'CH1\n负载阻抗\n值': main_window.doubleSpinBox_ch1_mode_inpedance_para.setValue(float(value))
                    case 'CH1\n负载阻抗\n单位': main_window.comboBox_ch1_mode_inpedance_unit.setCurrentText(value)
                    case 'CH1\n反相': main_window.checkBox_ch1_reverse.setChecked(bool(value))

                    # SMU 2410
                    case '2410-1\n保护电流\nw_protectionCurrentInput': main_window.w_protectionCurrentInput.setValue(float(value))
                    case '2410-1\n保护电流单位\nw_comboBox': main_window.w_comboBox.setCurrentText(value)
                    case '2410-1\n输出电压\nw_outputVoltageInput': main_window.w_outputVoltageInput.setValue(float(value))
                    case '2410-1\n输出电压单位\nw_comboBox_2': main_window.w_comboBox_2.setCurrentText(value)

                    case '2410-2\n保护电压\nw_protectionVoltageInput': main_window.w_protectionVoltageInput.setValue(float(value))
                    case '2410-2\n保护电压单位\nw_chooseSizeOfProtectionVoltage': main_window.w_chooseSizeOfProtectionVoltage.setCurrentText(value)
                    case '2410-2\n输出电流\nw_outputCurrentInput': main_window.w_outputCurrentInput.setValue(float(value))
                    case '2410-2\n输出电流单位\nw_comboBox_3': main_window.w_comboBox_3.setCurrentText(value)

                    case '2410-4\n扫描模式\nw_chooseSourceOfSweep': main_window.w_chooseSourceOfSweep.setCurrentText(value)
                    case '2410-4\n扫描方式\nw_chooseTypeOfSweep': main_window.w_chooseTypeOfSweep.setCurrentText(value)
                    case '2410-4\n起始\nw_SweepStartInput': main_window.w_SweepStartInput.setValue(float(value))
                    case '2410-4\n起始单位\nw_chooseSizeOfStartInput': main_window.w_chooseSizeOfStartInput.setCurrentText(value)
                    case '2410-4\n终止\nw_SweepEndInput': main_window.w_SweepEndInput.setValue(float(value))
                    case '2410-4\n终止单位\nw_chooseSizeOfEndInput': main_window.w_chooseSizeOfEndInput.setCurrentText(value)
                    case '2410-4\n步长点数\nw_SweepStepInput': main_window.w_SweepStepInput.setValue(float(value))
                    case '2410-4\n步长单位\nw_chooseSizeOfStepInput': main_window.w_chooseSizeOfStepInput.setCurrentText(value)
                    case '2410-4\n保护\nw_SweepIVProtectionInput': main_window.w_SweepIVProtectionInput.setValue(float(value))
                    case '2410-4\n保护单位\nw_chooseSizeOfSweepIVProtection': main_window.w_chooseSizeOfSweepIVProtection.setCurrentText(value)
                    case '2410-4\n测量延时\nw_SweepDelayInput': main_window.w_SweepDelayInput.setValue(float(value))
                    case '2410-4\n测量延时单位\nw_chooseSizeOfSweepDelay': main_window.w_chooseSizeOfSweepDelay.setCurrentText(value)



            # 关闭对话框并提示成功
            QMessageBox.information(self, "成功", "参数已加载到界面！")
            self.close()
            saveload_dialog.close()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败：{str(e)}")
