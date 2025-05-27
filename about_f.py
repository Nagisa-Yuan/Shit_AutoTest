"""""""""""""""""""""""""""""""""
Dialog_about相关函数
如你所见，这里面什么也没有

"""""""""""""""""""""""""""""""""

from PyQt5.QtWidgets import QMainWindow,QApplication,QDialog,QTableWidget, QTableWidgetItem, QScrollArea
from about import Ui_Dialog_about

class Dialog_about(QDialog, Ui_Dialog_about):
    def __init__(self, parent=None):
        super().__init__(parent)  # 设置窗口为模态（阻塞父窗口）
        self.setupUi(self)  # 初始化UI