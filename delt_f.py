"""""""""""""""""""""""""""""""""
Dialog_del相关函数
主要用于删除excel表中的一行

"""""""""""""""""""""""""""""""""
from PyQt5.QtWidgets import QMainWindow,QApplication,QDialog,QTableWidget, QTableWidgetItem, QScrollArea
import sys
from Auto_test_UI import Ui_Dialog  # 主界面
from saveload import Ui_Dialog_saveload  # 保存加载界面
from save import Ui_Dialog_save  # 保存加载的保存界面
from load import Ui_Dialog_load  # 保存加载的确认界面
from delt import Ui_Dialog_del  # 保存加载的删除界面
from datetime import datetime  # 获取当前时间


from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem
import pandas as pd
import os









class Dialog_del(QDialog, Ui_Dialog_del):
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
            self.textBrowser_del_name.setText(name_item.text())
        if remark_item:
            self.textBrowser_del_remark.setText(remark_item.text())


        # 连接按钮和函数
        self.pushButton_del_cancel.clicked.connect(self.del_cancel)  # 按下cancel
        self.pushButton_del_del.clicked.connect(self.del_del)  # 按下delete


    # 连接按钮的函数
    def del_cancel(self):
        self.close()

    def del_del(self):
        # 获取父窗口引用
        parent_saveload = self.parent()
        if not parent_saveload:
            QMessageBox.critical(self, "错误", "无法获取父窗口！")
            return

        selected_row = parent_saveload.tableWidget_saveload.currentRow()
        try:
            # 读取Excel文件
            current_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(current_dir, 'preset_data.xlsx')
            df = pd.read_excel(file_path, engine='openpyxl')

            # 删除对应行
            df = df.drop(selected_row).reset_index(drop=True)

            # 保存回Excel
            df.to_excel(file_path, index=False, engine='openpyxl')

            # 刷新父窗口表格
            parent_saveload.load_excel_to_table()

            QMessageBox.information(self, "成功", "删除成功！")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")

