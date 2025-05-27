"""""""""""""""""""""""""""""""""
Dialog_saveload相关函数

"""""""""""""""""""""""""""""""""
from PyQt5.QtWidgets import QMainWindow,QApplication,QDialog,QTableWidget, QTableWidgetItem, QScrollArea
import sys
from Auto_test_UI import Ui_Dialog  # 主界面
from saveload import Ui_Dialog_saveload  # 保存加载界面
from save_f import Dialog_save  # 保存加载的保存界面
from load_f import Dialog_load  # 保存加载的确认界面
from delt_f import Dialog_del  # 保存加载的删除界面
from datetime import datetime  # 获取当前时间


from qt_material import apply_stylesheet  # 界面美化库
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem
import pandas as pd
import os

class Dialog_saveload(QDialog, Ui_Dialog_saveload):
    def __init__(self, parent=None):
        super().__init__(parent)  # 设置窗口为模态（阻塞父窗口）
        self.setupUi(self)  # 初始化UI
        self.load_excel_to_table()  # 初始化时加载一次excel中的数据

        # 设置列宽：前三列120，其他列60
        # self.tableWidget_saveload.setColumnWidth(0, 120)  # 第1列
        # self.tableWidget_saveload.setColumnWidth(1, 120)  # 第2列
        # self.tableWidget_saveload.setColumnWidth(2, 120)  # 第3列
        for col in range(3, 20):  # 第4到6列
            self.tableWidget_saveload.setColumnWidth(col, 100)

        # 连接按钮和函数
        self.pushButton_saveload_save.clicked.connect(self.show_save_dialog)
        self.pushButton_saveload_load.clicked.connect(self.show_load_dialog)
        self.pushButton_saveload_del.clicked.connect(self.show_del_dialog)
        self.pushButton_saveload_cancel.clicked.connect(self.cancel_saveload)

    # 连接按钮的函数
    def load_excel_to_table(self):
        try:
            # 获取当前脚本所在目录并定位Excel文件
            current_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(current_dir, 'preset_data.xlsx')

            # 读取Excel数据
            df = pd.read_excel(file_path, engine='openpyxl')

            # 设置表格维度
            self.tableWidget_saveload.setRowCount(df.shape[0])
            self.tableWidget_saveload.setColumnCount(df.shape[1])

            # 设置列标题（假设第一行为标题）
            self.tableWidget_saveload.setHorizontalHeaderLabels(df.columns.tolist())

            # 填充数据到表格
            for row_idx, row_data in df.iterrows():
                for col_idx, cell_value in enumerate(row_data):
                    # 处理NaN值为空字符串
                    if pd.isna(cell_value):
                        cell_value = ""
                    item = QTableWidgetItem(str(cell_value))
                    self.tableWidget_saveload.setItem(row_idx, col_idx, item)

            # 取消默认选中
            self.tableWidget_saveload.clearSelection()
            self.tableWidget_saveload.setCurrentCell(-1, -1)

        except FileNotFoundError:
            QMessageBox.critical(self, "错误", "未找到预设文件: preset_data.xlsx")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载数据时发生错误: {str(e)}")

    def show_save_dialog(self):
        dialog_save = Dialog_save(parent=self)  # 指定父对象
        dialog_save.setWindowTitle("是否确定保存当前存档？")  # 修改窗口标题
        dialog_save.exec()

    def show_load_dialog(self):
        selected_row = self.tableWidget_saveload.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请先选中要加载的存档！")
            return
        dialog_load = Dialog_load(parent=self)  # 指定父对象
        dialog_load.setWindowTitle("是否确定加载该存档？")  # 修改窗口标题
        dialog_load.exec()

    def show_del_dialog(self):
        selected_row = self.tableWidget_saveload.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "警告", "请先选中要删除的存档！")
            return
        dialog_del = Dialog_del(parent=self)  # 指定父对象
        dialog_del.setWindowTitle("是否确定删除该存档？")  # 修改窗口标题
        dialog_del.exec()

    def cancel_saveload(self):
        self.close()

