"""
Author:Shiyue Wang
Plot_Keithley2410.py
"""
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas    # pyQT5的画布
from matplotlib.dates import DateFormatter, AutoDateLocator
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QStackedWidget, QLabel
from PyQt5.QtDesigner import QPyDesignerCustomWidgetPlugin
from PyQt5 import QtCore, QtWidgets



####################################################### 电压源模式绘图组件 #####################################################
class voltagePlotWidget(QWidget):
    def __init__(self):             # 类初始化，继承 QWidget 创建自定义 Qt 控件，用于嵌入 Matplotlib 图形
        super().__init__()
        self.initUI()
        self.currentPlotType = "line" # 默认显示折线图
        # self.generate_test_data()
        self.loadData()

    def initUI(self):
        self.stackedWidget = QStackedWidget()                   # 创建堆栈式布局 切换视图

        self.figure, self.ax = plt.subplots(figsize=(10, 6))    # 创建Matplotlib折线图画布
        self.canvas = FigureCanvas(self.figure)                 # 嵌入Qt界面  FigureCanvas将Matplotlib画布转换为Qt控件，支持在pyQt中显示

        self.table = QTableWidget()                             # 初始化表格组件
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)  # 允许多选
        self.table.setSelectionBehavior(QTableWidget.SelectItems)  # 按单元格选择
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["时间", "电压(V)", "电流(A)", "电阻(Ohm)", "备注"])
        self.table.setAlternatingRowColors(True)  # 启用斑马纹
        self.table.verticalHeader().setVisible(False)  # 隐藏行号
        
        # 视图切换控件
        self.viewSwitch = QComboBox()
        self.viewSwitch.addItems(["折线图", "表格"])
        self.viewSwitch.currentTextChanged.connect(self.switchView)

        # 创建轴选择容器
        self.axis_container = QWidget()
        self.axis_controls = QHBoxLayout(self.axis_container)
        self.axis_controls.setSpacing(10)  # 主布局中各轴之间的间距
        self.axis_container.setContentsMargins(0, 0, 0, 0)  # 上下边距5px

        def create_axis_control(label, combo):
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)  # 消除子布局边距
            layout.setSpacing(6)  # 标签与下拉框间距（从5减少到3）
            lbl = QLabel(label)
            lbl.setFixedWidth(20)  # 固定标签宽度
            combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)  # 根据内容自动调整宽度
            combo.setMinimumWidth(120)  # 固定下拉框最小宽度
            layout.addWidget(lbl)
            layout.addWidget(combo)
            return container

        # x轴部分
        self.xAxisCombo = QComboBox()
        self.axis_controls.addWidget(create_axis_control("x", self.xAxisCombo))

        # y1轴部分
        self.y1AxisCombo = QComboBox()
        self.axis_controls.addWidget(create_axis_control("y1", self.y1AxisCombo))

        # y2轴部分
        self.y2AxisCombo = QComboBox()
        self.axis_controls.addWidget(create_axis_control("y2", self.y2AxisCombo))

        # 创建表格容器（包含表格和操作按钮）
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        # 创建操作按钮的水平布局
        btn_layout = QHBoxLayout()
        # 保存刷新按键
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.on_save)
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.on_refresh)
        self.delete_btn = QPushButton("删除选中行")
        self.delete_btn.clicked.connect(self.delete_selected_row)

        # 调整按钮布局
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.delete_btn)

        # 主布局管理
        table_layout.addLayout(btn_layout)
        table_layout.addWidget(self.table)
        self.stackedWidget.addWidget(self.canvas) # index0 折线图
        self.stackedWidget.addWidget(table_container) # index1 表格

        layout = QVBoxLayout()
        layout.addWidget(self.viewSwitch)
        layout.addWidget(self.axis_container)
        layout.addWidget(self.stackedWidget)
        self.setLayout(layout)

        # 将容器插入主布局
        # layout.insertWidget(1, self.axis_container)

        # 连接信号
        self.xAxisCombo.currentTextChanged.connect(self.updatePlot)
        self.y1AxisCombo.currentTextChanged.connect(self.updatePlot)
        self.y2AxisCombo.currentTextChanged.connect(self.updatePlot)

    def on_save(self):
        """保存按钮点击事件"""
        self.sync_table_data()
        self.save_to_excel()

    def on_refresh(self):
        """刷新按钮点击事件"""
        self.loadData()

    def delete_selected_row(self):
        """删除整行方法"""
        # 同步备注数据
        self.sync_table_data()

        # 获取所有选中单元格
        selected_indexes = self.table.selectionModel().selectedIndexes()
        if not selected_indexes:
            return

        # 提取唯一行号并逆序排序
        rows = sorted({index.row() for index in selected_indexes}, reverse=True)

        # 批量删除DataFrame数据
        self.df = self.df.drop(index=self.df.index[rows]).reset_index(drop=True)

        # 删除表格行（必须逆序操作）
        for row in rows:
            self.table.removeRow(row)

        # 保存数据
        self.save_to_excel()

    def sync_table_data(self):
        for row in range(self.table.rowCount()):
            if row >= len(self.df):
                continue
            note_item = self.table.item(row, 4)
            self.df.at[row, '备注'] = note_item.text() if note_item else ""

    def delete_selected_row(self):
        # 同步表格中的备注数据到DataFrame
        self.sync_table_data()

        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        # 获取要删除的行号（降序处理防止索引错位）
        rows = sorted({r.row() for r in selected_rows}, reverse=True)

        # 从表格中删除
        for row in rows:
            self.table.removeRow(row)

        # 从DataFrame中删除
        self.df = self.df.drop(self.df.index[rows]).reset_index(drop=True)

        # 保存到Excel
        self.save_to_excel()

    def sync_table_data(self):
        """同步表格中的备注数据到DataFrame"""
        for row in range(self.table.rowCount()):
            if row >= len(self.df):
                continue
            note_item = self.table.item(row, 4)  # 备注列是第4列
            self.df.at[row, '备注'] = note_item.text() if note_item else ""


    def loadData(self):
        try:
            self.df = pd.read_excel(
                'Log_SourceVData.xlsx',
                sheet_name='Measurements',
                engine= 'openpyxl',
                # parse_dates=['Timestamp'],  # 让pandas直接解析日期
                dtype={'Voltage(V)': float, 'Current(A)': float, 'Timestamp': str}
                # dtype = {'TimeStamp': str}
            )

            # 转换文本时间为datetime
            self.df['Timestamp'] = pd.to_datetime(
                self.df['Timestamp'],
                format='%Y-%m-%d %H:%M:%S',
                errors='coerce'
            )

            self.df.columns = self.df.columns.str.strip().str.replace(' ', '')
            column_mapping = {
                'timeStamp': 'Timestamp',  # 原列名可能有大小写/空格问题
                'voltage(V)': 'Voltage(V)',
                'current(A)': 'Current(A)',
                'resistor(Ohm)': 'Resistor(Ohm)'
            }
            # self.df.rename(columns=column_mapping, inplace=True, errors='ignore')
            self.df.rename(columns=lambda x: column_mapping.get(x.lower(), x), inplace=True)

            if 'Timestamp' in self.df.columns:
                invalid_mask = self.df['Timestamp'].isna()
                if invalid_mask.any():
                    # invalid_rows = self.df[invalid_mask].index.tolist()
                    # print(f"警告：时间格式无效的行：{invalid_rows}")
                    # # 可选：清除无效行
                    # self.df = self.df[~invalid_mask]
                    print(f"发现{invalid_mask.sum()}行无效时间数据")
                    self.df = self.df[~invalid_mask].reset_index(drop=True)

            # 5. 确保列结构正确
            expected_columns = ['Timestamp', 'Voltage(V)', 'Current(A)', 'Resistor(Ohm)', '备注']
            self.df = self.df.reindex(columns=expected_columns, fill_value='')

            # 6. 处理备注列
            self.df['备注'] = self.df.get('备注', '').astype(str).str.strip()

            # 7. 初始化轴选项
            numeric_cols = self.df.select_dtypes(include=np.number).columns.tolist()
            self.available_columns = {
                'x': ['Timestamp'] + numeric_cols,
                'y': numeric_cols
            }

            # 填充下拉框
            self.xAxisCombo.clear()
            self.xAxisCombo.addItems(self.available_columns['x'])

            self.y1AxisCombo.clear()
            self.y1AxisCombo.addItems(self.available_columns['y'])

            self.y2AxisCombo.clear()
            self.y2AxisCombo.addItems(['无'] + self.available_columns['y'])

            # 设置默认轴
            self.xAxisCombo.setCurrentText('Timestamp')
            self.y1AxisCombo.setCurrentText('Voltage(V)')
            self.y2AxisCombo.setCurrentText('Current(A)')

        except Exception as e:
            print(f"数据加载失败: {str(e)}")
            # self.df = pd.DataFrame(columns=["Timestamp", "Voltage(V)", "Current(A)", "Resistor(Ohm)", "备注"])
            self.df = pd.DataFrame(columns=expected_columns)

        self.updateView()

    def save_to_excel(self):
        """保存数据到Excel文件"""
        try:
            # 创建副本避免修改原始数据
            df_to_save = self.df.copy()
            # 将时间列转为指定格式字符串
            df_to_save['Timestamp'] = df_to_save['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            # 读取原有所有工作表（如果文件存在）
            existing_sheets = {}
            try:
                existing_sheets = pd.read_excel(
                    'Log_SourceVData.xlsx',
                    sheet_name=None,
                    engine='openpyxl',
                    dtype={'Voltage(V)': float, 'Current(A)': float}
                )
            except FileNotFoundError:
                pass  # 新文件无需读取旧数据

            # 更新目标工作表数据
            existing_sheets['Measurements'] = df_to_save.reindex(
                columns=['Timestamp', 'Voltage(V)', 'Current(A)', 'Resistor(Ohm)', '备注'],
                fill_value=''
            )
            # 写入所有工作表
            with pd.ExcelWriter(
                    'Log_SourceVData.xlsx',
                    engine='openpyxl',
                    mode='w'
            ) as writer:
                for sheet_name, sheet_data in existing_sheets.items():
                    sheet_data.to_excel(
                        writer,
                        sheet_name=sheet_name,
                        index=False,
                        columns=sheet_data.columns  # 保持原有列顺序
                    )
                    # 设置时间列为文本格式
                    worksheet = writer.sheets[sheet_name]
                    if 'Timestamp' in sheet_data.columns:
                        for cell in worksheet['A']:
                            cell.number_format = '@'

            print(f"数据已保存到 'Log_SourceVData.xlsx'")

        except PermissionError:
            print("错误：文件被其他程序占用，请关闭Excel后重试")
        except Exception as e:
            print(f"保存失败: {str(e)}")

    def switchView(self, view_name):  # 添加视图切换方法
        """切换视图"""
        self.currentPlotType = "line" if view_name == "折线图" else "table"
        self.updateView()

    def updatePlot(self):

        if self.df.empty:
            return

        if self.currentPlotType != "line":
            return

        # 彻底清理绘图环境
        self.figure.clf()  # 清空整个画布
        self.ax = self.figure.add_subplot(111)  # 重建主坐标系
        self.ax2 = None  # 重置次坐标系引用

        x_col = self.xAxisCombo.currentText()
        y1_col = self.y1AxisCombo.currentText()
        y2_col = self.y2AxisCombo.currentText()

        try:
            # ===== 新增校验1：必要列存在性检查 =====
            missing_cols = []
            if x_col not in self.df.columns:
                missing_cols.append(x_col)
            if y1_col not in self.df.columns:
                missing_cols.append(y1_col)
            if y2_col != '无' and y2_col not in self.df.columns:
                missing_cols.append(y2_col)
            if missing_cols:
                raise KeyError(f"缺失数据列: {missing_cols}")

            # ===== 主Y轴绘图 =====

            x_data = (pd.to_datetime(self.df[x_col])
                      if pd.api.types.is_datetime64_any_dtype(self.df[x_col])
                      else pd.to_numeric(self.df[x_col], errors='coerce'))

            color = 'tab:blue'
            line1, = self.ax.plot(
                x_data,
                pd.to_numeric(self.df[y1_col], errors='coerce'),
                color=color,
                marker='o',
                linestyle='-',
                label=y1_col,
                markersize=6
            )

            # ===== 新增日期格式化 =====
            if pd.api.types.is_datetime64_any_dtype(self.df[x_col]):
                # 设置紧凑日期格式（自动适应时间范围）
                locator = AutoDateLocator()
                formatter = DateFormatter('%Y-%m-%d\n%H:%M:%S')  # 无小数格式
                self.ax.xaxis.set_major_locator(locator)
                self.ax.xaxis.set_major_formatter(formatter)

                # 自动旋转日期标签
                self.figure.autofmt_xdate(rotation=45, ha='right')

            # self.ax.tick_params(axis='y', labelcolor=color)
            self.ax.set_xlabel(x_col, fontsize=10)  # 调整标签字体
            self.ax.set_ylabel(y1_col, color=color, fontsize=10)
            self.ax.tick_params(axis='both', labelsize=8)  # 统一刻度字号

            # ===== 次Y轴处理 =====
            lines = [line1]
            if y2_col != '无' and y2_col in self.df.columns:
                self.ax2 = self.ax.twinx()
                color = 'tab:red'

                line2, = self.ax2.plot(
                    pd.to_datetime(self.df[x_col]) if pd.api.types.is_datetime64_any_dtype(self.df[x_col])
                    else pd.to_numeric(self.df[x_col], errors='coerce'),
                    pd.to_numeric(self.df[y2_col], errors='coerce'),
                    color=color,
                    marker='s',
                    linestyle='--',
                    label=y2_col,
                    markersize=5,
                    markeredgewidth=0.5
                )
                # ax2.tick_params(axis='y', labelcolor=color)
                self.ax2.set_ylabel(y2_col, color=color, fontsize=10)
                self.ax2.tick_params(axis='y', labelsize=8)
                lines.append(line2)

            # ===== 智能图例布局 =====
            legend = self.ax.legend(
                handles=lines,
                labels=[l.get_label() for l in lines],
                loc='upper center' if len(lines) == 1 else 'upper left',
                bbox_to_anchor=(0.5, 1.15) if len(lines) == 1 else (0, 1.15),
                ncol=min(2, len(lines)),
                fontsize=9,
                framealpha=0.8,
                borderaxespad=0.5
            )
            # legend = self.ax.legend(
            #     handles=lines,
            #     labels=[l.get_label() for l in lines],
            #     loc='upper left',  # 固定左上定位
            #     bbox_to_anchor=(0.02, 1.05),  # 相对坐标偏移
            #     ncol=1,  # 单列显示
            #     fontsize=8,  # 缩小字体
            #     frameon=True,
            #     framealpha=0.9,
            #     borderpad=0.8  # 紧凑布局
            # )
            legend.set_visible(True)  # 强制显示

            # ===== 动态调整布局 =====
            self.figure.subplots_adjust(
                left=0.15,
                right=0.85 if self.ax2 else 0.92,
                top=0.85,
                bottom=0.15
            )
            # self.figure.autofmt_xdate(rotation=30, ha='center')  # 优化日期旋转
            if pd.api.types.is_datetime64_any_dtype(self.df[x_col]):
                self.figure.autofmt_xdate(rotation=30, ha='center')
        #
            # 异步刷新画布
            self.canvas.draw_idle()

        except KeyError as e:
            print(f"列选择错误: {str(e)}")
            print("可用数据列:", self.df.columns.tolist())
        except TypeError as e:
            print(f"数据类型错误: {str(e)}")
            print("各列数据类型:")
            print(self.df.dtypes)
        except Exception as e:
            print(f"绘图错误: {str(e)}")

    def updateView(self):               # 更新当前视图
        if self.currentPlotType == "line":
            self.stackedWidget.setCurrentIndex(0)  # 显示折线图
            self.axis_container.show()
            self.updatePlot()  # 改为调用统一的绘图方法
            self.axis_controls.parent().show()  # 显示轴选择控件

        else:  # 表格视图
            self.stackedWidget.setCurrentIndex(1)  # 显示表格
            self.axis_controls.parent().hide()  # 隐藏轴选择控件
            self.table.setRowCount(len(self.df))

            # 填充表格数据
            for row in range(len(self.df)):
                self.table.setItem(row, 0, QTableWidgetItem(self.df["Timestamp"].iloc[row].strftime("%Y-%m-%d %H:%M:%S")))
                self.table.setItem(row, 1, QTableWidgetItem(str(self.df["Voltage(V)"].iloc[row])))
                self.table.setItem(row, 2, QTableWidgetItem(str(self.df["Current(A)"].iloc[row])))
                self.table.setItem(row, 3, QTableWidgetItem(f"{self.df['Resistor(Ohm)'].iloc[row]:.2f} "))
                # 添加可编辑的备注列
                # remark_item = QTableWidgetItem("")
                remark_text = str(self.df['备注'].iloc[row]) if pd.notnull(self.df['备注'].iloc[row]) else ""
                remark_item = QTableWidgetItem(remark_text)
                remark_item.setFlags(remark_item.flags() | QtCore.Qt.ItemIsEditable)

                remark_item.setFlags(remark_item.flags() | QtCore.Qt.ItemIsEditable)  # 设为可编辑
                self.table.setItem(row, 4, remark_item)

            # 自动调整列宽
            self.table.resizeColumnsToContents()
            # 设置备注列最小宽度
            self.table.setColumnWidth(4, 200)  # 备注列固定200像素宽度

################################################################################################################################################
######################################################################电流源模式绘图###############################################################
################################################################################################################################################
class currentPlotWidget(QWidget):
    def __init__(self):  # 类初始化，继承 QWidget 创建自定义 Qt 控件，用于嵌入 Matplotlib 图形
        super().__init__()
        self.initUI()
        self.currentPlotType = "line"  # 默认显示折线图
        # self.generate_test_data()
        self.loadData()

    def initUI(self):
        self.stackedWidget = QStackedWidget()  # 创建堆栈式布局 切换视图

        self.figure, self.ax = plt.subplots(figsize=(10, 6))  # 创建Matplotlib折线图画布
        self.canvas = FigureCanvas(self.figure)  # 嵌入Qt界面  FigureCanvas将Matplotlib画布转换为Qt控件，支持在pyQt中显示

        self.table = QTableWidget()  # 初始化表格组件
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)  # 允许多选
        self.table.setSelectionBehavior(QTableWidget.SelectItems)  # 按单元格选择
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["时间", "电流(A)", "电压(V)", "备注"])
        self.table.setAlternatingRowColors(True)  # 启用斑马纹
        self.table.verticalHeader().setVisible(False)  # 隐藏行号

        # 视图切换控件
        self.viewSwitch = QComboBox()
        self.viewSwitch.addItems(["折线图", "表格"])
        self.viewSwitch.currentTextChanged.connect(self.switchView)

        # 创建轴选择容器
        self.axis_container = QWidget()
        self.axis_controls = QHBoxLayout(self.axis_container)
        self.axis_controls.setSpacing(10)  # 主布局中各轴之间的间距
        self.axis_container.setContentsMargins(0, 0, 0, 0)  # 上下边距5px

        def create_axis_control(label, combo):
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)  # 消除子布局边距
            layout.setSpacing(6)  # 标签与下拉框间距（从5减少到3）
            lbl = QLabel(label)
            lbl.setFixedWidth(20)  # 固定标签宽度
            combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)  # 根据内容自动调整宽度
            combo.setMinimumWidth(120)  # 固定下拉框最小宽度
            layout.addWidget(lbl)
            layout.addWidget(combo)
            return container

        # x轴部分
        self.xAxisCombo = QComboBox()
        self.axis_controls.addWidget(create_axis_control("x", self.xAxisCombo))

        # y1轴部分
        self.y1AxisCombo = QComboBox()
        self.axis_controls.addWidget(create_axis_control("y1", self.y1AxisCombo))

        # y2轴部分
        self.y2AxisCombo = QComboBox()
        self.axis_controls.addWidget(create_axis_control("y2", self.y2AxisCombo))

        # 创建表格容器（包含表格和操作按钮）
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        # 创建操作按钮的水平布局
        btn_layout = QHBoxLayout()
        # 保存刷新按键
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.on_save)
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.on_refresh)
        self.delete_btn = QPushButton("删除选中行")
        self.delete_btn.clicked.connect(self.delete_selected_row)

        # 调整按钮布局
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.delete_btn)

        # 主布局管理
        table_layout.addLayout(btn_layout)
        table_layout.addWidget(self.table)
        self.stackedWidget.addWidget(self.canvas)  # index0 折线图
        self.stackedWidget.addWidget(table_container)  # index1 表格

        layout = QVBoxLayout()
        layout.addWidget(self.viewSwitch)
        layout.addWidget(self.axis_container)
        layout.addWidget(self.stackedWidget)
        self.setLayout(layout)

        # 将容器插入主布局
        # layout.insertWidget(1, self.axis_container)

        # 连接信号
        self.xAxisCombo.currentTextChanged.connect(self.updatePlot)
        self.y1AxisCombo.currentTextChanged.connect(self.updatePlot)
        self.y2AxisCombo.currentTextChanged.connect(self.updatePlot)

    def on_save(self):
        """保存按钮点击事件"""
        self.sync_table_data()
        self.save_to_excel()

    def on_refresh(self):
        """刷新按钮点击事件"""
        self.loadData()

    def delete_selected_row(self):
        """删除整行方法"""
        # 同步备注数据
        self.sync_table_data()

        # 获取所有选中单元格
        selected_indexes = self.table.selectionModel().selectedIndexes()
        if not selected_indexes:
            return

        # 提取唯一行号并逆序排序
        rows = sorted({index.row() for index in selected_indexes}, reverse=True)

        # 批量删除DataFrame数据
        self.df = self.df.drop(index=self.df.index[rows]).reset_index(drop=True)

        # 删除表格行（必须逆序操作）
        for row in rows:
            self.table.removeRow(row)

        # 保存数据
        self.save_to_excel()

    def sync_table_data(self):  # 同步备注数据到DataFrame
        for row in range(self.table.rowCount()):
            if row >= len(self.df):
                continue
            note_item = self.table.item(row, 3)
            self.df.at[row, '备注'] = note_item.text() if note_item else ""

    def delete_selected_row(self):
        # 同步表格中的备注数据到DataFrame
        self.sync_table_data()

        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        # 获取要删除的行号（降序处理防止索引错位）
        rows = sorted({r.row() for r in selected_rows}, reverse=True)

        # 从表格中删除
        for row in rows:
            self.table.removeRow(row)

        # 从DataFrame中删除
        self.df = self.df.drop(self.df.index[rows]).reset_index(drop=True)

        # 保存到Excel
        self.save_to_excel()

    def sync_table_data(self):
        """同步表格中的备注数据到DataFrame"""
        for row in range(self.table.rowCount()):
            if row >= len(self.df):
                continue
            note_item = self.table.item(row, 4)  # 备注列是第4列
            self.df.at[row, '备注'] = note_item.text() if note_item else ""

    def loadData(self):
        try:
            self.df = pd.read_excel(
                'Log_SourceIData.xlsx',
                sheet_name='Measurements',
                engine='openpyxl',
                # parse_dates=['Timestamp'],  # 让pandas直接解析日期
                dtype={'Voltage(V)': float, 'Current(A)': float, 'Timestamp': str}
                # dtype = {'TimeStamp': str}
            )

            # 转换文本时间为datetime
            self.df['Timestamp'] = pd.to_datetime(
                self.df['Timestamp'],
                format='%Y-%m-%d %H:%M:%S',
                errors='coerce'
            )
            # 处理列名
            self.df.columns = self.df.columns.str.strip().str.replace(' ', '')
            column_mapping = {
                'timeStamp': 'Timestamp',  # 原列名可能有大小写/空格问题
                'current(A)': 'Current(A)',
                'voltage(V)': 'Voltage(V)'
            }
            self.df.rename(columns=lambda x: column_mapping.get(x.lower(), x), inplace=True)

            if 'Timestamp' in self.df.columns:
                invalid_mask = self.df['Timestamp'].isna()
                if invalid_mask.any():
                    print(f"发现{invalid_mask.sum()}行无效时间数据")
                    self.df = self.df[~invalid_mask].reset_index(drop=True)

            # 5. 确保列结构正确
            expected_columns = ['Timestamp', 'Current(A)', 'Voltage(V)', '备注']
            self.df = self.df.reindex(columns=expected_columns, fill_value='')

            # 6. 处理备注列
            self.df['备注'] = self.df.get('备注', '').astype(str).str.strip()

            # 7. 初始化轴选项
            numeric_cols = self.df.select_dtypes(include=np.number).columns.tolist()
            self.available_columns = {
                'x': ['Timestamp'] + numeric_cols,
                'y': numeric_cols
            }

            # 填充下拉框
            self.xAxisCombo.clear()
            self.xAxisCombo.addItems(self.available_columns['x'])
            self.y1AxisCombo.clear()
            self.y1AxisCombo.addItems(self.available_columns['y'])
            self.y2AxisCombo.clear()
            self.y2AxisCombo.addItems(['无'] + self.available_columns['y'])

            # 设置默认轴
            self.xAxisCombo.setCurrentText('Timestamp')
            self.y1AxisCombo.setCurrentText('Current(A)')
            self.y2AxisCombo.setCurrentText('Voltage(V)')

        except Exception as e:
            print(f"数据加载失败: {str(e)}")
            # self.df = pd.DataFrame(columns=["Timestamp", "Voltage(V)", "Current(A)", "Resistor(Ohm)", "备注"])
            # self.df = pd.DataFrame(columns=expected_columns)
            self.df = pd.DataFrame(columns=['Timestamp', 'Current(A)', 'Voltage(V)', '备注'])
        self.updateView()

    def save_to_excel(self):
        """保存数据到Excel文件"""
        try:
            # 创建副本避免修改原始数据
            df_to_save = self.df.copy()
            # 将时间列转为指定格式字符串
            df_to_save['Timestamp'] = df_to_save['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            # 读取原有所有工作表（如果文件存在）
            existing_sheets = {}
            try:
                existing_sheets = pd.read_excel(
                    'Log_SourceIData.xlsx',
                    sheet_name=None,
                    engine='openpyxl',
                    dtype={'Voltage(V)': float, 'Current(A)': float}
                )
            except FileNotFoundError:
                pass  # 新文件无需读取旧数据

            # 更新目标工作表数据
            existing_sheets['Measurements'] = df_to_save.reindex(
                columns=['Timestamp', 'Voltage(V)', 'Current(A)', 'Resistor(Ohm)', '备注'],
                fill_value=''
            )
            # 写入所有工作表
            with pd.ExcelWriter(
                    'Log_SourceIData.xlsx',
                    engine='openpyxl',
                    mode='w'
            ) as writer:
                for sheet_name, sheet_data in existing_sheets.items():
                    sheet_data.to_excel(
                        writer,
                        sheet_name=sheet_name,
                        index=False,
                        columns=sheet_data.columns  # 保持原有列顺序
                    )
                    # 设置时间列为文本格式
                    worksheet = writer.sheets[sheet_name]
                    if 'Timestamp' in sheet_data.columns:
                        for cell in worksheet['A']:
                            cell.number_format = '@'

            print(f"数据已保存到 'Log_SourceIData.xlsx'")

        except PermissionError:
            print("错误：文件被其他程序占用，请关闭Excel后重试")
        except Exception as e:
            print(f"保存失败: {str(e)}")

    def switchView(self, view_name):  # 添加视图切换方法
        """切换视图"""
        self.currentPlotType = "line" if view_name == "折线图" else "table"
        self.updateView()

    def updatePlot(self):

        if self.df.empty:
            return
        if self.currentPlotType != "line":
            return

        # 彻底清理绘图环境
        self.figure.clf()  # 清空整个画布
        self.ax = self.figure.add_subplot(111)  # 重建主坐标系
        self.ax2 = None  # 重置次坐标系引用

        x_col = self.xAxisCombo.currentText()
        y1_col = self.y1AxisCombo.currentText()
        y2_col = self.y2AxisCombo.currentText()

        try:
            # ===== 新增校验1：必要列存在性检查 =====
            missing_cols = []
            if x_col not in self.df.columns:
                missing_cols.append(x_col)
            if y1_col not in self.df.columns:
                missing_cols.append(y1_col)
            if y2_col != '无' and y2_col not in self.df.columns:
                missing_cols.append(y2_col)
            if missing_cols:
                raise KeyError(f"缺失数据列: {missing_cols}")

            # ===== 主Y轴绘图 =====

            x_data = (pd.to_datetime(self.df[x_col])
                      if pd.api.types.is_datetime64_any_dtype(self.df[x_col])
                      else pd.to_numeric(self.df[x_col], errors='coerce'))

            color = 'tab:blue'
            line1, = self.ax.plot(
                x_data,
                pd.to_numeric(self.df[y1_col], errors='coerce'),
                color=color,
                marker='o',
                linestyle='-',
                label=y1_col,
                markersize=6
            )

            # ===== 新增日期格式化 =====
            if pd.api.types.is_datetime64_any_dtype(self.df[x_col]):
                # 设置紧凑日期格式（自动适应时间范围）
                locator = AutoDateLocator()
                formatter = DateFormatter('%Y-%m-%d\n%H:%M:%S')  # 无小数格式
                self.ax.xaxis.set_major_locator(locator)
                self.ax.xaxis.set_major_formatter(formatter)

                # 自动旋转日期标签
                self.figure.autofmt_xdate(rotation=45, ha='right')

            # self.ax.tick_params(axis='y', labelcolor=color)
            self.ax.set_xlabel(x_col, fontsize=10)  # 调整标签字体
            self.ax.set_ylabel(y1_col, color=color, fontsize=10)
            self.ax.tick_params(axis='both', labelsize=8)  # 统一刻度字号

            # ===== 次Y轴处理 =====
            lines = [line1]
            if y2_col != '无' and y2_col in self.df.columns:
                self.ax2 = self.ax.twinx()
                color = 'tab:red'

                line2, = self.ax2.plot(
                    pd.to_datetime(self.df[x_col]) if pd.api.types.is_datetime64_any_dtype(self.df[x_col])
                    else pd.to_numeric(self.df[x_col], errors='coerce'),
                    pd.to_numeric(self.df[y2_col], errors='coerce'),
                    color=color,
                    marker='s',
                    linestyle='--',
                    label=y2_col,
                    markersize=5,
                    markeredgewidth=0.5
                )
                # ax2.tick_params(axis='y', labelcolor=color)
                self.ax2.set_ylabel(y2_col, color=color, fontsize=10)
                self.ax2.tick_params(axis='y', labelsize=8)
                lines.append(line2)

            # ===== 智能图例布局 =====
            legend = self.ax.legend(
                handles=lines,
                labels=[l.get_label() for l in lines],
                loc='upper center' if len(lines) == 1 else 'upper left',
                bbox_to_anchor=(0.5, 1.15) if len(lines) == 1 else (0, 1.15),
                ncol=min(2, len(lines)),
                fontsize=9,
                framealpha=0.8,
                borderaxespad=0.5
            )
            # legend = self.ax.legend(
            #     handles=lines,
            #     labels=[l.get_label() for l in lines],
            #     loc='upper left',  # 固定左上定位
            #     bbox_to_anchor=(0.02, 1.05),  # 相对坐标偏移
            #     ncol=1,  # 单列显示
            #     fontsize=8,  # 缩小字体
            #     frameon=True,
            #     framealpha=0.9,
            #     borderpad=0.8  # 紧凑布局
            # )
            legend.set_visible(True)  # 强制显示

            # ===== 动态调整布局 =====
            self.figure.subplots_adjust(
                left=0.15,
                right=0.85 if self.ax2 else 0.92,
                top=0.85,
                bottom=0.15
            )
            # self.figure.autofmt_xdate(rotation=30, ha='center')  # 优化日期旋转
            if pd.api.types.is_datetime64_any_dtype(self.df[x_col]):
                self.figure.autofmt_xdate(rotation=30, ha='center')
            #
            # 异步刷新画布
            self.canvas.draw_idle()

        except KeyError as e:
            print(f"列选择错误: {str(e)}")
            print("可用数据列:", self.df.columns.tolist())
        except TypeError as e:
            print(f"数据类型错误: {str(e)}")
            print("各列数据类型:")
            print(self.df.dtypes)
        except Exception as e:
            print(f"绘图错误: {str(e)}")

    def updateView(self):  # 更新当前视图
        if self.currentPlotType == "line":
            self.stackedWidget.setCurrentIndex(0)  # 显示折线图
            self.axis_container.show()
            self.updatePlot()  # 改为调用统一的绘图方法
            self.axis_controls.parent().show()  # 显示轴选择控件

        else:  # 表格视图
            self.stackedWidget.setCurrentIndex(1)  # 显示表格
            self.axis_controls.parent().hide()  # 隐藏轴选择控件
            self.table.setRowCount(len(self.df))

            # 填充表格数据
            for row in range(len(self.df)):
                self.table.setItem(row, 0,
                                   QTableWidgetItem(self.df["Timestamp"].iloc[row].strftime("%Y-%m-%d %H:%M:%S")))
                self.table.setItem(row, 1, QTableWidgetItem(str(self.df["Current(A)"].iloc[row])))
                self.table.setItem(row, 2, QTableWidgetItem(str(self.df["Voltage(V)"].iloc[row])))
                # 添加可编辑的备注列
                # remark_item = QTableWidgetItem("")
                remark_text = str(self.df['备注'].iloc[row]) if pd.notnull(self.df['备注'].iloc[row]) else ""
                remark_item = QTableWidgetItem(remark_text)
                remark_item.setFlags(remark_item.flags() | QtCore.Qt.ItemIsEditable)

                remark_item.setFlags(remark_item.flags() | QtCore.Qt.ItemIsEditable)  # 设为可编辑
                self.table.setItem(row, 3, remark_item)

            # 自动调整列宽
            self.table.resizeColumnsToContents()
            # 设置备注列最小宽度
            self.table.setColumnWidth(3, 200)  # 备注列固定200像素宽度

################################################################################################################################################
#################################################################### 脉冲模式预览图 ###############################################################
################################################################################################################################################

class PulsePreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.figure.tight_layout(pad=2.0)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.canvas)

        # 初始化默认参数
        self.high_level = 1.0
        self.low_level = 0.0
        self.pulse_width = 1.0
        self.duty_cycle = 0.5
        self.num_pulses = 1

    def update_preview(self, params):
        """根据脉冲参数更新波形预览"""
        try:
            # 解析参数
            self.high_level = params.get('high', 1.0)
            self.low_level = params.get('low', 0.0)
            self.pulse_width = params.get('width', 1.0)
            self.duty_cycle = params.get('duty', 0.5) / 100  # 转换为小数
            self.num_pulses = params.get('num', 1)

            # 计算周期和生成波形
            period = self.pulse_width / self.duty_cycle
            t = np.linspace(0, self.num_pulses * period, 1000)
            waveform = self.low_level * np.ones_like(t)

            # 生成脉冲波形
            for i in range(self.num_pulses):
                start = i * period
                end = start + self.pulse_width
                mask = (t >= start) & (t <= end)
                waveform[mask] = self.high_level

            # 清空并重绘
            self.ax.clear()
            self.ax.plot(t, waveform, 'b-', linewidth=2)
            self.ax.set_xlabel('Time (s)')
            self.ax.set_ylabel('Amplitude (V)')
            self.ax.grid(True)
            self.canvas.draw()

        except Exception as e:
            print(f"波形生成错误: {str(e)}")


################################################################################################################################################
#################################################################### 扫描模式表格 ###############################################################
################################################################################################################################################

class SweepWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.loadData()

    def initUI(self):
        layout = QVBoxLayout()

        # 添加模式选择
        mode_layout = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["电压扫描", "电流扫描"])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(QLabel("显示模式:"))
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()

        # 操作按钮布局
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.loadData)
        btn_layout.addLayout(mode_layout)
        btn_layout.addStretch()
        btn_layout.addWidget(self.refresh_btn)

        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
             "电压(V)", "电流(A)", "合规状态"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def on_mode_changed(self):
        """切换显示模式时重新加载数据"""
        self.loadData()

    def get_current_sheet(self):
        """获取当前选择的sheet名称"""
        return "Voltage" if self.mode_combo.currentText() == "电压扫描" else "Current"

    def loadData(self):
        try:
            # 读取当前选择的sheet数据
            sheet_name = self.get_current_sheet()
            self.df = pd.read_excel(
                'Log_SweepData.xlsx',
                sheet_name=sheet_name,  # 动态读取选择的sheet
                engine='openpyxl',
                dtype={
                    'voltage': float,
                    'current': float,
                    'status_raw_value': int
                }
            )

            # 标准化列名（兼容不同sheet的列名格式）
            self.df.columns = self.df.columns.str.strip().str.lower()
            column_mapping = {
                'voltage': '电压(V)',
                'current': '电流(A)',
                'status_is_compliance': '合规状态'
            }
            self.df.rename(columns=column_mapping, inplace=True, errors='ignore')

            # 填充表格
            self.table.setRowCount(len(self.df))
            for row in range(len(self.df)):
                self.table.setItem(row, 0, QTableWidgetItem(f"{self.df.iloc[row]['电压(V)']:.6f}"))
                self.table.setItem(row, 1, QTableWidgetItem(f"{self.df.iloc[row]['电流(A)']:.6f}"))
                self.table.setItem(row, 2, QTableWidgetItem("是" if self.df.iloc[row]['合规状态'] else "否"))

            self.table.resizeColumnsToContents()

        except FileNotFoundError:
            print("未找到扫描数据文件")
            self.table.setRowCount(0)
        except KeyError as e:
            print(f"Sheet {sheet_name} 不存在: {str(e)}")
            self.table.setRowCount(0)
        except Exception as e:
            print(f"数据加载失败: {str(e)}")
            self.table.setRowCount(0)