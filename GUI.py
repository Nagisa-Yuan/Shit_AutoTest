"""""""""""""""""""""""""""""""""
main函数和主窗口MyWindow相关函数


"""""""""""""""""""""""""""""""""
from PyQt5.QtWidgets import QMainWindow,QApplication,QDialog,QTableWidget, QTableWidgetItem, QScrollArea
import sys
from test2 import Ui_MainWindow  # 主界面
from about import Ui_Dialog_about  # 保存加载界面
from save import Ui_Dialog_save  # 保存加载的保存界面
from load import Ui_Dialog_load  # 保存加载的确认界面
from delt import Ui_Dialog_del  # 保存加载的删除界面
from datetime import datetime  # 获取当前时间


from Generator_control import AFG3102C  # AFG3102C控制函数
from Generator_control import AFG31102  # AFG31102控制函数

from qt_material import apply_stylesheet  # 界面美化库
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem
import pandas as pd
import os

from saveload_f import Dialog_saveload
from about_f import Dialog_about



class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()  # 继承父类
        self.setupUi(self)  # 初始化UI

        # 连接按钮和函数
        self.pushButton_ch1_ON.clicked.connect(self.ch1_ON)
        self.pushButton_ch1_OFF.clicked.connect(self.ch1_OFF)
        self.pushButton_ch1_setPara.clicked.connect(self.set_para)
        self.comboBox_ch1_mode_mode.currentIndexChanged.connect(self.ch1_mode_combo_changed)
        self.comboBox_ch2_mode_mode.currentIndexChanged.connect(self.ch2_mode_combo_changed)
        self.pushButton_saveload.clicked.connect(self.show_saveload_dialog)
        self.pushButton_about.clicked.connect(self.show_about_dialog)


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
        AFG1.output_on(1)
    def ch1_OFF(self):
        AFG1.output_off(1)

    def ch2_ON(self):  # 开启/关闭ch2输出
        AFG1.output_on(1)
    def ch2_OFF(self):
        AFG1.output_off(1)

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


    def set_para(self):  # 设置ch1参数
        try:
            # 读取负载阻抗
            ch1_mode_inpedance_para = self.doubleSpinBox_ch1_mode_inpedance_para.value()
            ch1_mode_inpedance_unit = self.comboBox_ch1_mode_inpedance_unit.currentText()
            ch1_mode_inpedance_unit_multiplier = {
                'Ω': 1,     # Ω
                'kΩ': 1e3,  # kΩ → Ω
            }.get(ch1_mode_inpedance_unit, 1)  # 默认为Ω，无需转换
            # ================================================选中正弦波======================================================
            if (self.tabWidget_ch1_wave.currentIndex() == 0):  # 选中正弦波
                if (self.tabWidget_ch1_sine_freq.currentIndex() == 0):  # 选中频率
                    # 读取频率
                    ch1_sine_freq_freq_value = self.doublespinBox_ch1_sine_freq_freq_para.value()
                    ch1_sine_freq_freq_unit = self.comboBox_ch1_sine_freq_freq_unit.currentText()
                    ch1_sine_freq_freq_unit_multiplier = {
                        'Hz': 1,     # Hz
                        'kHz': 1e3,  # kHz → Hz
                        'MHz': 1e6,  # MHz → Hz
                    }.get(ch1_sine_freq_freq_unit, 1)  # 默认为Hz，无需转换
                    # 计算频率：数值*单位
                    ch1_sine_freq_freq_value_out = ch1_sine_freq_freq_value * ch1_sine_freq_freq_unit_multiplier
                elif (self.tabWidget_ch1_sine_freq.currentIndex() == 1): # 选中周期
                    # 读取周期
                    ch1_sine_freq_cycle_value = self.doublespinBox_ch1_sine_freq_cycle_para.value()
                    ch1_sine_freq_cycle_unit = self.comboBox_ch1_sine_freq_cycle_unit.currentText()
                    ch1_sine_freq_cycle_unit_multiplier = {
                        's': 1,      # s
                        'ms': 1e-3,  # ms → s
                        'μs': 1e-6,  # μs → s
                        'ns': 1e-9,  # ns → s
                    }.get(ch1_sine_freq_cycle_unit, 1)  # 默认为s，无需转换
                    # 计算周期：数值*单位, 周期 → 频率
                    ch1_sine_freq_freq_value_out = 1/(ch1_sine_freq_cycle_value * ch1_sine_freq_cycle_unit_multiplier)


                if (self.tabWidget_ch1_sine_vol.currentIndex() == 0):  # 选中高-低电平
                    # 读取高电平
                    ch1_sine_vol_hlvol_hpara = self.doubleSpinBox_ch1_sine_vol_hlvol_hpara.value()
                    ch1_sine_vol_hlvol_hunit = self.comboBox_ch1_sine_vol_hlvol_hunit.currentText()
                    ch1_sine_vol_hlvol_hunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,      # V
                    }.get(ch1_sine_vol_hlvol_hunit, 1)  # 默认为V，无需转换
                    # 读取低电平
                    ch1_sine_vol_hlvol_lpara = self.doubleSpinBox_ch1_sine_vol_hlvol_lpara.value()
                    ch1_sine_vol_hlvol_lunit = self.comboBox_ch1_sine_vol_hlvol_lunit.currentText()
                    ch1_sine_vol_hlvol_lunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,      # V
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
                        'V': 1,      # V
                    }.get(ch1_sine_vol_appoff_appunit, 1)  # 默认为V，无需转换
                    # 读取偏置
                    ch1_sine_vol_appoff_offvalue = self.doubleSpinBox_ch1_sine_vol_appoff_offpara.value()
                    ch1_sine_vol_appoff_offunit = self.comboBox_ch1_sine_vol_appoff_offunit.currentText()
                    ch1_sine_vol_appoff_offunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,      # V
                    }.get(ch1_sine_vol_appoff_offunit, 1)  # 默认为V，无需转换

                    # 计算电平：数值*单位, 高-低电平 → 幅度-偏置
                    ch1_sine_vol_hlvol_hout = ch1_sine_vol_appoff_offvalue * ch1_sine_vol_appoff_offunit_multiplier + 0.5 * ch1_sine_vol_appoff_appvalue * ch1_sine_vol_appoff_appunit_multiplier
                    ch1_sine_vol_hlvol_lout = ch1_sine_vol_appoff_offvalue * ch1_sine_vol_appoff_offunit_multiplier - 0.5 * ch1_sine_vol_appoff_appvalue * ch1_sine_vol_appoff_appunit_multiplier

                # 设置正弦波形
                AFG1.setwave_sine(1, ch1_sine_vol_hlvol_hout, ch1_sine_vol_hlvol_lout, ch1_sine_freq_freq_value_out)

            # ================================================选中方波======================================================
            elif (self.tabWidget_ch1_wave.currentIndex() == 1):  # 选中方波
                if (self.tabWidget_ch1_square_freq.currentIndex() == 0):  # 选中频率
                    # 读取频率
                    ch1_square_freq_freq_value = self.doublespinBox_ch1_square_freq_freq_para.value()
                    ch1_square_freq_freq_unit = self.comboBox_ch1_square_freq_freq_unit.currentText()
                    ch1_square_freq_freq_unit_multiplier = {
                        'Hz': 1,     # Hz
                        'kHz': 1e3,  # kHz → Hz
                        'MHz': 1e6,  # MHz → Hz
                    }.get(ch1_square_freq_freq_unit, 1)  # 默认为Hz，无需转换
                    # 计算频率：数值*单位
                    ch1_square_freq_freq_value_out = ch1_square_freq_freq_value * ch1_square_freq_freq_unit_multiplier
                elif (self.tabWidget_ch1_square_freq.currentIndex() == 1): # 选中周期
                    # 读取周期
                    ch1_square_freq_cycle_value = self.doublespinBox_ch1_square_freq_cycle_para.value()
                    ch1_square_freq_cycle_unit = self.comboBox_ch1_square_freq_cycle_unit.currentText()
                    ch1_square_freq_cycle_unit_multiplier = {
                        's': 1,      # s
                        'ms': 1e-3,  # ms → s
                        'μs': 1e-6,  # μs → s
                        'ns': 1e-9,  # ns → s
                    }.get(ch1_square_freq_cycle_unit, 1)  # 默认为s，无需转换
                    # 计算周期：数值*单位, 周期 → 频率
                    ch1_square_freq_freq_value_out = 1/(ch1_square_freq_cycle_value * ch1_square_freq_cycle_unit_multiplier)


                if (self.tabWidget_ch1_square_vol.currentIndex() == 0):  # 选中高-低电平
                    # 读取高电平
                    ch1_square_vol_hlvol_hpara = self.doubleSpinBox_ch1_square_vol_hlvol_hpara.value()
                    ch1_square_vol_hlvol_hunit = self.comboBox_ch1_square_vol_hlvol_hunit.currentText()
                    ch1_square_vol_hlvol_hunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,      # V
                    }.get(ch1_square_vol_hlvol_hunit, 1)  # 默认为V，无需转换
                    # 读取低电平
                    ch1_square_vol_hlvol_lpara = self.doubleSpinBox_ch1_square_vol_hlvol_lpara.value()
                    ch1_square_vol_hlvol_lunit = self.comboBox_ch1_square_vol_hlvol_lunit.currentText()
                    ch1_square_vol_hlvol_lunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,      # V
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
                        'V': 1,      # V
                    }.get(ch1_square_vol_appoff_appunit, 1)  # 默认为V，无需转换
                    # 读取偏置
                    ch1_square_vol_appoff_offvalue = self.doubleSpinBox_ch1_square_vol_appoff_offpara.value()
                    ch1_square_vol_appoff_offunit = self.comboBox_ch1_square_vol_appoff_offunit.currentText()
                    ch1_square_vol_appoff_offunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,      # V
                    }.get(ch1_square_vol_appoff_offunit, 1)  # 默认为V，无需转换

                    # 计算电平：数值*单位, 高-低电平 → 幅度-偏置
                    ch1_square_vol_hlvol_hout = ch1_square_vol_appoff_offvalue * ch1_square_vol_appoff_offunit_multiplier + 0.5 * ch1_square_vol_appoff_appvalue * ch1_square_vol_appoff_appunit_multiplier
                    ch1_square_vol_hlvol_lout = ch1_square_vol_appoff_offvalue * ch1_square_vol_appoff_offunit_multiplier - 0.5 * ch1_square_vol_appoff_appvalue * ch1_square_vol_appoff_appunit_multiplier

                # 设置方波形
                AFG1.setwave_square(1, ch1_square_vol_hlvol_hout, ch1_square_vol_hlvol_lout, ch1_square_freq_freq_value_out)
                
            # ================================================选中PWM波======================================================
            elif (self.tabWidget_ch1_wave.currentIndex() == 2):  # 选中PWM波
                if (self.tabWidget_ch1_PWM_freq.currentIndex() == 0):  # 选中频率
                    # 读取频率
                    ch1_PWM_freq_freq_value = self.doublespinBox_ch1_PWM_freq_freq_para.value()
                    ch1_PWM_freq_freq_unit = self.comboBox_ch1_PWM_freq_freq_unit.currentText()
                    ch1_PWM_freq_freq_unit_multiplier = {
                        'Hz': 1,     # Hz
                        'kHz': 1e3,  # kHz → Hz
                        'MHz': 1e6,  # MHz → Hz
                    }.get(ch1_PWM_freq_freq_unit, 1)  # 默认为Hz，无需转换
                    # 计算频率：数值*单位
                    ch1_PWM_freq_freq_value_out = ch1_PWM_freq_freq_value * ch1_PWM_freq_freq_unit_multiplier
                elif (self.tabWidget_ch1_PWM_freq.currentIndex() == 1): # 选中周期
                    # 读取周期
                    ch1_PWM_freq_cycle_value = self.doublespinBox_ch1_PWM_freq_cycle_para.value()
                    ch1_PWM_freq_cycle_unit = self.comboBox_ch1_PWM_freq_cycle_unit.currentText()
                    ch1_PWM_freq_cycle_unit_multiplier = {
                        's': 1,      # s
                        'ms': 1e-3,  # ms → s
                        'μs': 1e-6,  # μs → s
                        'ns': 1e-9,  # ns → s
                    }.get(ch1_PWM_freq_cycle_unit, 1)  # 默认为s，无需转换
                    # 计算周期：数值*单位, 周期 → 频率
                    ch1_PWM_freq_freq_value_out = 1/(ch1_PWM_freq_cycle_value * ch1_PWM_freq_cycle_unit_multiplier)


                if (self.tabWidget_ch1_PWM_vol.currentIndex() == 0):  # 选中高-低电平
                    # 读取高电平
                    ch1_PWM_vol_hlvol_hpara = self.doubleSpinBox_ch1_PWM_vol_hlvol_hpara.value()
                    ch1_PWM_vol_hlvol_hunit = self.comboBox_ch1_PWM_vol_hlvol_hunit.currentText()
                    ch1_PWM_vol_hlvol_hunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,      # V
                    }.get(ch1_PWM_vol_hlvol_hunit, 1)  # 默认为V，无需转换
                    # 读取低电平
                    ch1_PWM_vol_hlvol_lpara = self.doubleSpinBox_ch1_PWM_vol_hlvol_lpara.value()
                    ch1_PWM_vol_hlvol_lunit = self.comboBox_ch1_PWM_vol_hlvol_lunit.currentText()
                    ch1_PWM_vol_hlvol_lunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,      # V
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
                        'V': 1,      # V
                    }.get(ch1_PWM_vol_appoff_appunit, 1)  # 默认为V，无需转换
                    # 读取偏置
                    ch1_PWM_vol_appoff_offvalue = self.doubleSpinBox_ch1_PWM_vol_appoff_offpara.value()
                    ch1_PWM_vol_appoff_offunit = self.comboBox_ch1_PWM_vol_appoff_offunit.currentText()
                    ch1_PWM_vol_appoff_offunit_multiplier = {
                        'mV': 1e-3,  # mV → V
                        'V': 1,      # V
                    }.get(ch1_PWM_vol_appoff_offunit, 1)  # 默认为V，无需转换

                    # 计算电平：数值*单位, 高-低电平 → 幅度-偏置
                    ch1_PWM_vol_hlvol_hout = ch1_PWM_vol_appoff_offvalue * ch1_PWM_vol_appoff_offunit_multiplier + 0.5 * ch1_PWM_vol_appoff_appvalue * ch1_PWM_vol_appoff_appunit_multiplier
                    ch1_PWM_vol_hlvol_lout = ch1_PWM_vol_appoff_offvalue * ch1_PWM_vol_appoff_offunit_multiplier - 0.5 * ch1_PWM_vol_appoff_appvalue * ch1_PWM_vol_appoff_appunit_multiplier

                # 读取占空比
                ch1_PWM_duty = self.doubleSpinBox_ch1_PWM_duty.value()

                # 设置PWM波形
                AFG1.setwave_PWM(1, ch1_PWM_vol_hlvol_hout, ch1_PWM_vol_hlvol_lout, ch1_PWM_freq_freq_value_out, ch1_PWM_duty)

            else:
                QMessageBox.information(self, "error", "error")


            # 发送指令，在仪器上设置上述读取的参数
            # 设置反相
            if (self.checkBox_ch1_reverse.isChecked()):
                AFG1.set_reverse(1, 1)
            else:
                AFG1.set_reverse(1, 0)


            # 设置负载阻抗
            if(ch1_mode_inpedance_unit == '高阻抗'):
                AFG1.set_impedance_highZ(1)
            else:
                AFG1.set_impedance(1, ch1_mode_inpedance_para * ch1_mode_inpedance_unit_multiplier)



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
                AFG1.setwave_sine(1, ch1_sine_vol_hlvol_hout, ch1_sine_vol_hlvol_lout, ch1_sine_freq_freq_value_out)

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
                AFG1.setwave_square(1, ch1_square_vol_hlvol_hout, ch1_square_vol_hlvol_lout,
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
                AFG1.setwave_PWM(1, ch1_PWM_vol_hlvol_hout, ch1_PWM_vol_hlvol_lout, ch1_PWM_freq_freq_value_out,
                                 ch1_PWM_duty)

            else:
                QMessageBox.information(self, "error", "error")

            # 发送指令，在仪器上设置上述读取的参数
            # 设置反相
            if (self.checkBox_ch1_reverse.isChecked()):
                AFG1.set_reverse(1, 1)
            else:
                AFG1.set_reverse(1, 0)

            # 设置负载阻抗
            if (ch1_mode_inpedance_unit == '高阻抗'):
                AFG1.set_impedance_highZ(1)
            else:
                AFG1.set_impedance(1, ch1_mode_inpedance_para * ch1_mode_inpedance_unit_multiplier)

            QMessageBox.information(self, "成功", "信号发生器参数设置成功!")

        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))






if __name__ == "__main__":
    # AFG1 = AFG31102('GPIB0::10::INSTR')
    # AFG1 = AFG3102C('GPIB0::11::INSTR')



    app = QApplication(sys.argv)  # 实例QApplication


    # 使用自定义的主窗口类
    dialog = MyWindow()



    # # 应用界面美化主题
    # extra = {
    #     'font_size': '10px',
    #     'font_family': 'TimesNewRoman',  # 可选：修改字体类型
    # }
    # apply_stylesheet(
    #     app,
    #     theme='light_teal_500.xml',
    #     extra=extra  # 注入自定义配置
    # )


    dialog.setWindowTitle("信号发生器控制")  # 修改窗口标题
    dialog.show()

    sys.exit(app.exec_())

















