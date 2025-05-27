"""""""""""""""""""""""""""""""""
Dialog_save相关函数
用于将参数写入excel表

"""""""""""""""""""""""""""""""""
from PyQt5.QtWidgets import QMainWindow,QApplication,QDialog,QTableWidget, QTableWidgetItem, QScrollArea
import sys
from Auto_test_UI import Ui_Dialog  # 主界面
from saveload import Ui_Dialog_saveload  # 保存加载界面
from save import Ui_Dialog_save  # 保存加载的保存界面
from load import Ui_Dialog_load  # 保存加载的确认界面
from delt import Ui_Dialog_del  # 保存加载的删除界面
from datetime import datetime  # 获取当前时间
# from saveload_f import Dialog_saveload

from openpyxl.utils import get_column_letter  # 导入列字母转换函数


from qt_material import apply_stylesheet  # 界面美化库
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem
import pandas as pd

import os











class Dialog_save(QDialog, Ui_Dialog_save):
    def __init__(self, parent=None):
        super().__init__(parent)  # 设置窗口为模态（阻塞父窗口）
        self.setupUi(self)  # 初始化UI

        # 连接按钮和函数
        self.pushButton_save_save.clicked.connect(self.save_save)
        self.pushButton_save_cancel.clicked.connect(self.save_cancel)

    # 连接按钮的函数
    def save_cancel(self):
        self.close()

    def save_save(self):
        name = self.lineEdit_save_name.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "名称不能为空！")
            return

        remark = self.lineEdit_save_remark.text().strip()
        current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        # 获取主窗口中的所有参数
        try:
            # 获取父窗口层级：self(Dialog_save) → parent(Dialog_saveload) → parent(MyWindow)
            parent_saveload = self.parent()
            main_window = parent_saveload.parent()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"参数获取失败: {str(e)}")
            return

        # 将数据翻译为表中的汉字
        wave_mapping = {
            0: '正弦波',
            1: '方波',
            2: 'PWM波'
        }
        mode_mode_mapping = {
            0: 'Continuous',
            1: 'Burst',
        }
        tab_ch1_wave = wave_mapping.get(main_window.tabWidget_ch1_wave.currentIndex(), '未选择')
        tab_ch1_mode_mode = mode_mode_mapping.get(main_window.comboBox_ch1_mode_mode.currentIndex(), '未选择')
        tab_ch2_wave = wave_mapping.get(main_window.tabWidget_ch2_wave.currentIndex(), '未选择')
        tab_ch2_mode_mode = mode_mode_mapping.get(main_window.comboBox_ch2_mode_mode.currentIndex(), '未选择')


        try:
            file_path = os.path.join(os.path.dirname(__file__), 'preset_data.xlsx')
            new_data = pd.DataFrame([{
                '时间': current_time,
                '名称': name,
                '备注': remark,
                'CH1\n输出模式': tab_ch1_mode_mode,
                'CH1\n波形': tab_ch1_wave,
                'CH2\n输出模式': tab_ch2_mode_mode,
                'CH2\n波形': tab_ch2_wave,

                '2410\n模式': main_window.tabWidget.currentIndex(),
                '2430\n模式': main_window.kei2430tabWidget.currentIndex(),

                'CH1\n正弦波\n频率值': main_window.doublespinBox_ch1_sine_freq_freq_para.value(),
                'CH1\n正弦波\n频率单位': main_window.comboBox_ch1_sine_freq_freq_unit.currentText(),
                'CH1\n正弦波\n高电平值': main_window.doubleSpinBox_ch1_sine_vol_hlvol_hpara.value(),
                'CH1\n正弦波\n高电平单位': main_window.comboBox_ch1_sine_vol_hlvol_hunit.currentText(),
                'CH1\n正弦波\n低电平值': main_window.doubleSpinBox_ch1_sine_vol_hlvol_lpara.value(),
                'CH1\n正弦波\n低电平单位': main_window.comboBox_ch1_sine_vol_hlvol_lunit.currentText(),

                'CH1\n方波\n频率值': main_window.doublespinBox_ch1_square_freq_freq_para.value(),
                'CH1\n方波\n频率单位':  main_window.comboBox_ch1_square_freq_freq_unit.currentText(),
                'CH1\n方波\n高电平值': main_window.doubleSpinBox_ch1_square_vol_hlvol_hpara.value(),
                'CH1\n方波\n高电平单位': main_window.comboBox_ch1_square_vol_hlvol_hunit.currentText(),
                'CH1\n方波\n低电平值': main_window.doubleSpinBox_ch1_square_vol_hlvol_lpara.value(),
                'CH1\n方波\n低电平单位': main_window.comboBox_ch1_square_vol_hlvol_lunit.currentText(),

                'CH1\nPWM波\n频率值': main_window.doublespinBox_ch1_PWM_freq_freq_para.value(),
                'CH1\nPWM波\n频率单位': main_window.comboBox_ch1_PWM_freq_freq_unit.currentText(),
                'CH1\nPWM波\n高电平值': main_window.doubleSpinBox_ch1_PWM_vol_hlvol_hpara.value(),
                'CH1\nPWM波\n高电平单位': main_window.comboBox_ch1_PWM_vol_hlvol_hunit.currentText(),
                'CH1\nPWM波\n低电平值': main_window.doubleSpinBox_ch1_PWM_vol_hlvol_lpara.value(),
                'CH1\nPWM波\n低电平单位': main_window.comboBox_ch1_PWM_vol_hlvol_lunit.currentText(),
                'CH1\nPWM波\n占空比': main_window.doubleSpinBox_ch1_PWM_duty.value(),

                'CH1\n负载阻抗\n值': main_window.doubleSpinBox_ch1_mode_inpedance_para.value(),
                'CH1\n负载阻抗\n单位': main_window.comboBox_ch1_mode_inpedance_unit.currentText(),
                'CH1\n反相': main_window.checkBox_ch1_reverse.isChecked(),

                # ch2


                # SMU 面向用户


                # # SMU 2410 面向程序员
                '2410-1\n保护电流\nw_protectionCurrentInput': float(main_window.w_protectionCurrentInput.toPlainText()),
                # '2410-1\n保护电流单位\nw_comboBox': main_window.w_comboBox.currentIndex(),
                # '2410-1\n输出电压\nw_outputVoltageInput': float(main_window.w_outputVoltageInput.toPlainText()),
                # '2410-1\n输出电压单位\nw_comboBox_2': main_window.w_comboBox_2.currentIndex(),
                # '2410-2\n保护电压\nw_protectionVoltageInput': float(main_window.w_protectionVoltageInput.toPlainText()),
                # '2410-2\n保护电压单位\nw_chooseSizeOfProtectionVoltage': main_window.w_chooseSizeOfProtectionVoltage.currentIndex(),
                # '2410-2\n输出电流\nw_outputCurrentInput': float(main_window.w_outputCurrentInput.toPlainText()),
                # '2410-2\n输出电流单位\nw_comboBox_3': main_window.w_comboBox_3.currentIndex(),
                # '2410-4\n扫描模式\nw_chooseSourceOfSweep': main_window.w_chooseSourceOfSweep.currentIndex(),
                # '2410-4\n扫描方式\nw_chooseTypeOfSweep': main_window.w_chooseTypeOfSweep.currentIndex(),
                # '2410-4\n起始\nw_SweepStartInput': float(main_window.w_SweepStartInput.toPlainText()),
                # '2410-4\n起始单位\nw_chooseSizeOfStartInput': main_window.w_comboBox_3.currentIndex(),





            }])

            df = pd.read_excel(file_path, engine='openpyxl')
            df = pd.concat([new_data, df], ignore_index=True)

            # 使用ExcelWriter调整列宽，统一为20
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
                worksheet = writer.sheets['Sheet1']
                for col_idx in range(df.shape[1]):  # 遍历所有列
                    col_letter = get_column_letter(col_idx + 1)  # 将列索引转为字母（从A开始）
                    worksheet.column_dimensions[col_letter].width = 20  # 统一宽度

            QMessageBox.information(self, "成功", "保存成功！")
            self.close()

            # 刷新父窗口表格
            parent = self.parent()
            parent.load_excel_to_table()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败：{str(e)}")

