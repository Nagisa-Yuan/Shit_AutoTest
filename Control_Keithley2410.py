"""
Author:Shiyue Wang
Control_Keithley2410.py
"""
""""""""""""""""""""""""""""""""""
封装函数介绍:
testIO(self):                                           #测试仪器通信
set_current_protection(self, current):                  #设置电流保护阈值
set_voltage_protection(self, vol):                      #设置电压量程保护
set_voltage(self, vol, speed=1):                        #带渐变功能的安全设置电压 vol是目标电压
show_voltage(self):                                     #读取当前电压值
sweep(self, vols, vole, step, speed):                   #电压渐变总控制方案 vols是当前电压 vole是目标电压 单位V
sweep_forward(self, vols, vole, step, speed):           #升压
sweep_backward(self, vols, vole, step, speed):          #降压
display_current(self):                                  #显示当前电流值
hit_compliance(self):                                   #检查是否触发电流保护
ramp_down(self):                                        #安全降压到0V
output_on(self):                                        #启用输出
output_off(self):                                       #停止输出
beep(self, freq=1046.50, duration=0.3):                 #发出提示音
filter_on(self, count=20, mode="repeat"):               #启用测量滤波
filter_off(self):                                       #关闭测量滤波

"""""""""""""""""""""""""""""""""


import pyvisa
import time
import warnings
import pandas as pd
import os
import numpy


class keithley2410:
    def __init__(self, resource_name):                          #初始化函数，建立与仪器的连接 与Keithley2410连接要输入 'GPIB0::08::INSTR'
        self.instlist = pyvisa.ResourceManager()
        self.kei2410 = self.instlist.open_resource(resource_name)    #打开keithley2410的仪器资源（.open_resource('GPIB0::08::INSTR')）f"ASRL3::INSTR"
        self.kei2410.baud_rate = 9600
        self.kei2410.data_bits = 8
        self.kei2410.stop_bits = pyvisa.constants.StopBits.one
        self.kei2410.parity = pyvisa.constants.Parity.none
        self.kei2410.flow_control = pyvisa.constants.ControlFlow.none
        # my_instrument.flow_control = visa.constants.ControlFlow.rts_cts
        self.kei2410.read_termination = '\r'
        self.kei2410.write_termination = '\r'
        self.kei2410.timeout = 5000  # 单位毫秒
        self.kei2410.write('*RST')
        time.sleep(2)  # 等待复位完成
        self.outputOff()  # 确保输出关闭

        # 配置仪器使用前或后面板端子
        # self.kei2410.write(":ROUTe:TERMinals FRONt") # FRONT  #配置前面板
        # self.kei2410.write(":ROUTe:TERMinals REAR")  # REAR     #配置后面板 后面板端子通常用于高精度自动化测试
        self.sourceVDataBase = pd.DataFrame(columns=["TimeStamp", "Voltage(V)", "Current(A)", "Resistor(Ohm)"]) # 建立电压源模式数据容器
        self.sourceIDataBase = pd.DataFrame(columns=["TimeStamp", "Current(A)", "Voltage(V)"])
        self.kei2410.timeout = 25000                            #设置超时时间为25s
        self.globalCurrentProtection = '105E-6'  # global current protection       #设置全局电流保护值默认值105uA
        self.sweep_done = False

    #############################基本功能函数#################################

    def safe_initialize(self):
        try:
            self.outputOff()
            self.setCurrentProtection(105e-6)
            self.directSetVoltageOutput(0)
        except Exception as e:
            print(f"初始化安全措施失败: {str(e)}")

    def testIO(self):                                           #测试仪器通信
        message = self.kei2410.query('*IDN?')                   #正常会返回：KEITHLEY INSTRUMENTS INC.,MODEL 2410,4406455,C34 Sep 21 2016 15:30:00/A02  /L/M
        print(message)

    def outputOn(self):                                        #启用输出
        self.kei2410.write(":output on")
        print("Output on")

    def outputOff(self):                                       #停止输出
        self.kei2410.write(":output off")
        print("Output off")

    def get_output_state(self):
        """获取当前输出状态"""
        return self.kei2410.query(":OUTPUT?").strip() == '1'

    def directSetVoltageOutput(self, vol):
        self.kei2410.write(":source:voltage:level "+str(vol))

    def directSetCurrentOutput(self, curr):
        self.kei2410.write(":source:current:level " + str(curr))

    def showVoltage(self):                                     #读取当前电压值
        # source_mode = self.kei2410.query(":source:function?").strip().lower()
        data = self.kei2410.query(":read?").split(',')
        voltage = data[0]
        print("voltage [V]: " + str(voltage))
        return float(voltage)

    def showCurrent(self):                                     #读取当前电压值
        # source_mode = self.kei2410.query(":source:function?").strip().lower()
        data = self.kei2410.query(":read?").split(',')
        current = data[1]
        print("current [A]: " + str(current))
        return float(current)

    def beep(self, freq=1046.50, duration=0.3):                 #发出提示音
        self.kei2410.write(":system:beeper " + str(freq) + ", " + str(duration))
        time.sleep(duration)

    def resetInstruments(self):
        self.kei2410.write('*RST')
        time.sleep(0.1)  # 等待复位完成

    #############################读写存储相关函数#################################

    # def recordOnceDataSourceV(self):        # 记录一次电压源模式数据
    #     voltage = self.showVoltage()
    #     current = self.showCurrent()
    #     resistor = 0
    #     newRow = {
    #         "Timestamp" : pd.Timestamp.now(),
    #         "Voltage(V)" : voltage,
    #         "Current(A)" : current,
    #         "Resistor(Ohm)" : resistor
    #     }
    #     self.sourceVDataBase = pd.concat([self.sourceVDataBase , pd.DataFrame([newRow])], ignore_index= True)
    #
    # def save2ExcelSourceV(self, filename="Log_SourceVData.xlsx"):  # 将当前列中数据记录至excel表格
    #     try:
    #         # 创建数据副本避免修改原始数据
    #         df_to_save = self.sourceVDataBase.copy()
    #         # 转换时间戳为字符串
    #         df_to_save['Timestamp'] = df_to_save['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    #         # 添加备注列（如果不存在）
    #         if '备注' not in df_to_save.columns:
    #             df_to_save['备注'] = ''
    #         # 列顺序
    #         columns = ['Timestamp', 'Voltage(V)', 'Current(A)', 'Resistor(Ohm)', '备注']
    #
    #         # 使用 xlsxwriter 引擎写入
    #         with pd.ExcelWriter(filename, engine='openpyxl') as writer:
    #             df_to_save.to_excel(
    #                 writer,
    #                 sheet_name='Measurements',
    #                 index=False,
    #                 columns=columns
    #             )
    #             workbook = writer.book
    #             worksheet = writer.sheets['Measurements']
    #
    #         print(f"successfully saved to {filename}")
    #     except PermissionError:
    #         print("错误：文件被占用，请关闭Excel后重试")
    #     except Exception as e:
    #         print(f"保存失败: {str(e)}")
    #
    # def recordOnceDataSourceI(self):  # 记录一次电流源模式数据
    #     voltage = self.showVoltage()
    #     current = self.showCurrent()
    #     newRow = {
    #         "Timestamp": pd.Timestamp.now(),
    #         "Current(A)": current,
    #         "Voltage(V)": voltage
    #     }
    #     self.sourceIDataBase = pd.concat([self.sourceIDataBase, pd.DataFrame([newRow])], ignore_index=True)
    #
    # def save2ExcelSourceI(self, filename="Log_SourceIData.xlsx"):  # 将当前列中数据记录至excel表格
    #     try:
    #         # 创建数据副本避免修改原始数据
    #         df_to_save = self.sourceIDataBase.copy()
    #         # 转换时间戳为字符串
    #         df_to_save['Timestamp'] = df_to_save['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    #         # 添加备注列（如果不存在）
    #         if '备注' not in df_to_save.columns:
    #             df_to_save['备注'] = ''
    #         # 列顺序
    #         columns = ['Timestamp', 'Current(A)', 'Voltage(V)', '备注']
    #
    #         # 使用 openpyxl 引擎写入
    #         with pd.ExcelWriter(filename, engine='openpyxl') as writer:
    #             df_to_save.to_excel(
    #                 writer,
    #                 sheet_name='Measurements',
    #                 index=False,
    #                 columns=columns
    #             )
    #             workbook = writer.book
    #             worksheet = writer.sheets['Measurements']
    #
    #         print(f"successfully saved to {filename}")
    #     except PermissionError:
    #         print("错误：文件被占用，请关闭Excel后重试")
    #     except Exception as e:
    #         print(f"保存失败: {str(e)}")


    def saveCurrentSweepData(self, filename="Log_SweepData.xlsx"):
        """保存电流扫描数据到Excel文件的Current工作表中"""
        try:
            # 读取扫描数据
            structured_data = self.readSweepData()
            print(structured_data)              ############### 测试用
            if not structured_data:
                print("无扫描数据可保存")
                return

            # 将嵌套数据结构转换为平面DataFrame
            df = pd.json_normalize(structured_data, sep='_')

            # 添加系统时间戳（整个保存操作的时间）
            df.insert(0, "Save_Timestamp", pd.Timestamp.now())

            # 处理现有Excel文件（如果存在）
            sheets = {}
            if os.path.isfile(filename):
                try:
                    with pd.ExcelFile(filename) as excel:
                        sheets = {sheet: pd.read_excel(excel, sheet_name=sheet)
                                  for sheet in excel.sheet_names if sheet != 'Current'}
                except Exception as e:
                    print(f"读取现有文件时发生警告: {str(e)}")

            # 使用openpyxl引擎写入数据（支持.xlsx格式）
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # 保留原有工作表（排除Current）
                for sheet_name, data in sheets.items():
                    data.to_excel(writer, sheet_name=sheet_name, index=False)
                # 写入当前数据到Current工作表
                df.to_excel(writer, sheet_name='Current', index=False)

            print(f"扫描数据已成功保存至 {filename} 的 [Current] 工作表")

        except PermissionError:
            print("错误：文件被占用，请关闭Excel后重试")
        except Exception as e:
            print(f"保存过程中发生错误: {str(e)}")

    def saveVoltageSweepData(self, filename="Log_SweepData.xlsx"):
        """保存电流扫描数据到Excel文件的Current工作表中"""
        try:
            # 读取扫描数据
            structured_data = self.readSweepData()
            if not structured_data:
                print("无扫描数据可保存")
                return

            # 将嵌套数据结构转换为平面DataFrame
            df = pd.json_normalize(structured_data, sep='_')

            # 添加系统时间戳（整个保存操作的时间）
            df.insert(0, "Save_Timestamp", pd.Timestamp.now())

            # 处理现有Excel文件（如果存在）
            sheets = {}
            if os.path.isfile(filename):
                try:
                    with pd.ExcelFile(filename) as excel:
                        sheets = {sheet: pd.read_excel(excel, sheet_name=sheet)
                                  for sheet in excel.sheet_names if sheet != 'Voltage'}
                except Exception as e:
                    print(f"读取现有文件时发生警告: {str(e)}")

            # 使用openpyxl引擎写入数据（支持.xlsx格式）
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # 保留原有工作表（排除Current）
                for sheet_name, data in sheets.items():
                    data.to_excel(writer, sheet_name=sheet_name, index=False)
                # 写入当前数据到Current工作表
                df.to_excel(writer, sheet_name='Voltage', index=False)

            print(f"扫描数据已成功保存至 {filename} 的 [Voltage] 工作表")

        except PermissionError:
            print("错误：文件被占用，请关闭Excel后重试")
        except Exception as e:
            print(f"保存过程中发生错误: {str(e)}")

    #############################电压源模式相关函数#################################

    def setSourceVoltage(self):
        self.kei2410.write(":source:function voltage")
        self.kei2410.write(":sense:function 'current'")

    def setCurrentProtection(self, current):                  #设置电流保护阈值
        self.globalCurrentProtection = str(current)
        self.kei2410.write(":sense:current:protection " + str(current))

    def setVoltage(self, targetVol, speed=1):                        #带渐变功能的安全设置电压 vol是目标电压
        self.kei2410.write(":sense:current:protection " + self.globalCurrentProtection)#设置全局电流保护值默认值105uA
        self.kei2410.write(":source:function voltage")          #配置为电压源模式
        self.kei2410.write(":source:voltage:mode fixed")        #电压源的输出模式设置为固定输出模式
        print("******************************")
        print("From")
        currentVol = self.showVoltage()                              #获取当前电压值
        print("******************************")

        #分段电压渐变逻辑 避免调整电压时出现过大的电压阶跃
        if -10 <= targetVol <= 10 and -10 <= currentVol <= 10:              #目前电压vols和目标电压vol都在安全电压范围 步长1V
            self.sweep(currentVol, targetVol, 1, speed)
        elif -10 <= targetVol <= 10 and currentVol < -10:                   #目前电压不在安全区（<-10V） 目标电压在安全区 分两步调整 vols→-10V（大步长10V），然后-10V→vol（步长1V）
            self.sweep(currentVol, -10, 10, speed)
            self.sweep(-10, targetVol, 1, speed)
        elif -10 <= targetVol <= 10 and currentVol > 10:                    #目前电压不在安全区（>-10V） 目标电压在安全区 分两步：vols→10V（大步长10V），然后10V→vol（步长1V）
            self.sweep(currentVol, 10, 10, speed)
            self.sweep(10, targetVol, 1, speed)
        elif targetVol < -10 and -10 <= currentVol <= 10:                   #
            self.sweep(currentVol, -10, 1, speed)
            self.sweep(-10, targetVol, 10, speed)
        elif targetVol > 10 and -10 <= currentVol <= 10:
            self.sweep(currentVol, 10, 1, speed)
            self.sweep(10, targetVol, 10, speed)
        else:
            self.sweep(currentVol, targetVol, 10, speed)


        print("******************************")
        print("To")
        vols = self.showVoltage()
        print("******************************")
        self.beep()                                             #操作完成提示音
        return vols

    def sweep(self, currentVol, targetVol, step, speed):                   #电压渐变总控制方案 vols是当前电压 vole是目标电压 单位V
        if currentVol < targetVol:  # vol start < vol end
            self.sweepForwardVoltage(currentVol, targetVol, step, speed)
        else:
            self.sweepBackwardVoltage(currentVol, targetVol, step, speed)

    def sweepForwardVoltage(self, currentVol, targetVol, stepVol, speed):           #升压
        # Conveter from V to uV 提高精度
        uCurrentVol = currentVol * 1000000
        uTargetVol = targetVol * 1000000 + 1                                 #？+1确保包含最终值
        uStepVol = stepVol * 1000000
        self.kei2410.write("source:voltage:level " + str(currentVol))       # 备用 可删
        for uvol in range(int(uCurrentVol), int(uTargetVol), int(uStepVol)):  #这是个循环
            vol = uvol / 1000000  # uV -> V
            self.kei2410.write(":source:voltage:level " + str(vol))
            time.sleep(5 / speed)
            self.showVoltage()
            # self.display_current()
            self.hitComplianceCurrent()                               #合规性检查
        self.kei2410.write(":source:voltage:level " + str(targetVol))

    def sweepBackwardVoltage(self, currentVol, targetVol, stepVol, speed):          #降压
        # Conveter from V to uV
        uCurrentVol = currentVol * 1000000-1
        uTargetVol = targetVol * 1000000 - 1000
        uStepVol = stepVol * 1000000
        self.kei2410.write("source:voltage:level " + str(currentVol))  # 备用 可删
        for uvol in range(int(uCurrentVol), int(uTargetVol), -int(uStepVol)):
            vol = uvol / 1000000  # uV -> V
            self.kei2410.write(":source:voltage:level " + str(vol))
            time.sleep(5 / speed)
            self.showVoltage()
            # self.display_current()
            self.hitComplianceCurrent()
        self.kei2410.write(":source:voltage:level " + str(targetVol))

    def hitComplianceCurrent(self):                                   #检查是否触发电流保护
        tripped = int(str(self.kei2410.query(":SENSE:CURRENT:PROTECTION:TRIPPED?")))
        if tripped:
            print("Hit the compliance " + self.globalCurrentProtection + "A.")
        return tripped

    def rampDownVoltage(self):                                        #安全降压到0V
        print("Now ramping down...")
        self.setVoltage(0, 5)
        self.beep()

    #############################电压源脉冲模式相关函数#################################

    def voltagePulseMode1(self,cycle,pulseWidth,dutyCycle,high,low=0):          # pulseWidth的单位是s,精度在us级别，当cycle=0时为无线循环
        self.kei2410.write(":source:function voltage")
        highVol=str(high)
        lowVol=str(low)
        uPulseHighWidth = pulseWidth * dutyCycle * 10000
        uPulseLowWidth = pulseWidth * (100-dutyCycle) * 10000
        i = cycle
        if cycle == 0:
            while 1:
                startTime1 = time.perf_counter() * 1000000
                while (time.perf_counter() * 1000000 - startTime1) <= uPulseLowWidth:
                    self.kei2410.write(":source:voltage:level " + str(lowVol))

                startTime2 = time.perf_counter() * 1000000
                while (time.perf_counter() * 1000000 - startTime2) <= uPulseHighWidth:
                    self.kei2410.write(":source:voltage:level " + str(highVol))
        else:
            while i:
                startTime1 = time.perf_counter() * 1000000
                while (time.perf_counter() * 1000000 - startTime1) < uPulseLowWidth:
                    self.kei2410.write(":source:voltage:level " + str(lowVol))

                startTime2 = time.perf_counter() * 1000000
                while (time.perf_counter() * 1000000 - startTime2) < uPulseHighWidth:
                    self.kei2410.write(":source:voltage:level " + str(highVol))

                i -= 1


    def voltagePulseMode2(self,cycle,pulseWidth,dutyCycle,step,highStart,low=0):
        self.kei2410.write(":source:function voltage")
        i = 0
        uPulseHighWidth = pulseWidth * dutyCycle * 10000
        uPulseLowWidth = pulseWidth * (100 - dutyCycle) * 10000
        while cycle:
            highVol = highStart + step * i
            startTime1 = time.perf_counter() * 1000000
            while (time.perf_counter() * 1000000 - startTime1) < uPulseLowWidth:
                self.kei2410.write(":source:voltage:level " + str(low))
            startTime2 = time.perf_counter() * 1000000
            while (time.perf_counter() * 1000000 - startTime2) < uPulseHighWidth:
                self.kei2410.write(":source:voltage:level " + str(highVol))
            i += 1
            cycle -= 1

    def voltagePulseMode3(self):
        self.kei2410.write(":source:function voltage")
        pulse = [
            (0,1,2,50),(0,4,4,25),(2,8,6,33),(4,6,8,75)
        ]
        for low,high,pulseWidth,dutyCycle in pulse:
            self.voltageSinglePulse(low,high,pulseWidth,dutyCycle)

    def voltageSinglePulse(self,low,high,pulseWidth,dutyCycle):
        uPulseHighWidth = pulseWidth * dutyCycle * 10000
        uPulseLowWidth = pulseWidth * (100 - dutyCycle) * 10000
        startTime1 = time.perf_counter() * 1000000
        while (time.perf_counter() * 1000000 - startTime1) < uPulseLowWidth:
            self.kei2410.write(":source:voltage:level " + str(high))
        startTime2 = time.perf_counter() * 1000000
        while (time.perf_counter() * 1000000 - startTime2) < uPulseHighWidth:
            self.kei2410.write(":source:voltage:level " + str(low))

    #############################电流源模式相关函数#################################

    def setSourceCurrent(self):
        self.kei2410.write(":source:function current")
        self.kei2410.write(":sense:function 'voltage'")

    # def display_current(self):                                  #显示当前电流值
    #     self.kei2410.write(":sense:function 'current'")
    #     self.kei2410.write(":sense:current:range:auto on")      #自动量程
    #     self.kei2410.write(":display:enable on")                #启用显示屏
    #     self.kei2410.write(":display:digits 7")                 #显示7位数字
    #     self.kei2410.write(":form:elem current")                #返回格式仅电流
    #     current = self.kei2410.query(":read?")
    #     print("current [A]: " + str(current))
    #     return float(str(current))

    def setVoltageProtection(self, vol):                      #设置电压量程保护
        self.kei2410.write(":sense:voltage:protection " + str(vol))

    ############################# 扫描模式 #################################

    def CurrentSweep(self, sweep_type='linear', start=1e-3, stop=10e-3, step=1e-3, point=5, compliance=10, delay=0.5):
        self.kei2410.write(":TRAC:POIN 1000")  # 设置缓冲区大小
        self.kei2410.write(":TRAC:CLE")  # 清空缓冲区
        self.kei2410.write(":TRAC:FEED SENS")  # 存储测量数据
        if sweep_type == 'linear':
            # 计算扫描点数
            count = int((stop-start)/step) + 1
            # self.kei2410.write("*RST")
            self.kei2410.write(":sense:function:CONC OFF")
            self.kei2410.write(":source:function current")
            self.kei2410.write(":sense:function 'VOlT:DC'")
            self.kei2410.write(":sense:voltage:protection " + str(compliance))
            self.kei2410.write(":source:current:start " + str(start))
            self.kei2410.write(":source:current:stop " + str(stop))
            self.kei2410.write(":source:current:step " + str(step))
            self.kei2410.write(":source:current:mode sweep")
            self.kei2410.write(":SOUR:SWE:RANG AUTO")
            self.kei2410.write(":source:sweep:SPAC LIN")
            self.kei2410.write(":TRIG:COUN " + str(count))
            self.kei2410.write(":source:delay " + str(delay))
            self.kei2410.write(":OUTP ON")
            self.kei2410.write(":READ?")
        else:
            # self.kei2410.write("*RST")
            self.kei2410.write(":sense:function:CONC OFF")
            self.kei2410.write(":source:function current")
            self.kei2410.write(":sense:function 'VOlT:DC'")
            self.kei2410.write(":sense:voltage:protection " + str(compliance))
            self.kei2410.write(":source:current:start " + str(start))
            self.kei2410.write(":source:current:stop " + str(stop))
            self.kei2410.write(":source:current:mode sweep")
            self.kei2410.write(":SOUR:SWE:RANG AUTO")
            self.kei2410.write(":source:sweep:SPAC LOG")
            self.kei2410.write(":source:sweep:POINts " + str(point))
            self.kei2410.write(":TRIG:COUN " + str(point))
            self.kei2410.write(":source:delay " + str(delay))
            self.kei2410.write(":OUTP ON")
            self.kei2410.write(":READ?")
        # self.kei2410.query("*OPC?")  # 阻塞直到操作完成
        # time.sleep(20)
        self.sweep_done = True
        # data = self.readSweepData()
        # data = self.kei2410.read()
        # print(data)

    def VoltageSweep(self, sweep_type='linear', start=1, stop=10, step=1, point=5, compliance=12e-3, delay=0.5):
        self.kei2410.write(":TRAC:POIN 1000")  # 设置缓冲区大小
        self.kei2410.write(":TRAC:CLE")  # 清空缓冲区
        self.kei2410.write(":TRAC:FEED SENS")  # 存储测量数据
        if sweep_type == 'linear':
            # 计算扫描点数
            count = int((stop-start)/step) + 1
            # self.kei2410.write("*RST")
            self.kei2410.write(":sense:function:CONC OFF")
            self.kei2410.write(":source:function voltage")
            self.kei2410.write(":sense:function 'CURRENT:DC'")
            self.kei2410.write(":sense:current:protection " + str(compliance))
            self.kei2410.write(":source:voltage:start " + str(start))
            self.kei2410.write(":source:voltage:stop " + str(stop))
            self.kei2410.write(":source:voltage:step " + str(step))
            self.kei2410.write(":source:voltage:mode sweep")
            self.kei2410.write(":SOUR:SWE:RANG AUTO")
            self.kei2410.write(":source:sweep:SPAC LIN")
            self.kei2410.write(":TRIG:COUN " + str(count))
            self.kei2410.write(":source:delay " + str(delay))
            self.kei2410.write(":OUTP ON")
            self.kei2410.write(":READ?")
        else:
            # self.kei2410.write("*RST")
            count = int(point) + 1
            self.kei2410.write(":sense:function:CONC OFF")
            self.kei2410.write(":source:function voltage")
            self.kei2410.write(":sense:function 'CURRENT:DC'")
            self.kei2410.write(":sense:current:protection " + str(compliance))
            self.kei2410.write(":source:voltage:start " + str(start))
            self.kei2410.write(":source:voltage:stop " + str(stop))
            self.kei2410.write(":source:voltage:mode sweep")
            self.kei2410.write(":SOUR:SWE:RANG AUTO")
            self.kei2410.write(":source:sweep:SPAC LOG")
            self.kei2410.write(":source:sweep:POINts " + str(point))
            self.kei2410.write(":TRIG:COUN " + str(point))
            self.kei2410.write(":source:delay " + str(delay))
            self.kei2410.write(":OUTP ON")
            self.kei2410.write(":READ?")
        # self.kei2410.query("*OPC?")  # 阻塞直到操作完成 加上对read产生重大打击
        # data = self.kei2410.read()    # read测试用
        self.sweep_done = True
        # print(data)


    def readSweepData(self):
        """读取当前扫描数据，返回结构化数据"""
        try:
            # 读取原始数据字符串（自动触发仪器发送缓存数据）
            raw_data = self.kei2410.read()
            print(raw_data)
            # 分割分号，只保留数据部分（部分仪器会在末尾添加";1"表示结束）
            if ';' in raw_data:
                raw_data = raw_data.split(';')[0]
            # 按逗号分割数据（数据格式：电压,电流,电阻,时间,状态）
            data_points = raw_data.strip().split(',')
            self.kei2410.write(":OUTP OFF")
            # 校验数据完整性（每个扫描点应包含5个字段）
            if len(data_points) % 5 != 0:
                raise ValueError(f"数据格式错误，总字段数{len(data_points)}不是5的倍数")

            num_points = len(data_points) // 5
            structured_data = []

            for i in range(num_points):
                idx = i * 5
                try:
                    # 转换状态寄存器值（关键修改）
                    status_float = float(data_points[idx + 4])  # 先转为浮点数
                    status_int = int(status_float)  # 再转为整数

                    point = {
                        "voltage": float(data_points[idx]),  # 电压 (V)
                        "current": float(data_points[idx + 1]),  # 电流 (A)
                        "resistance": float(data_points[idx + 2]),  # 电阻 (Ω)
                        "timestamp": float(data_points[idx + 3]),  # 时间戳 (s)
                        "status": {
                            "raw_value": status_int,  # 原始整数值
                            "binary": bin(status_int),  # 二进制表示
                            "is_compliance": bool(status_int & 0x04)  # 示例：检查合规触发位
                        }
                    }
                    structured_data.append(point)

                except (IndexError, ValueError) as ve:
                    print(f"数据点{i}解析失败: {str(ve)}")
                    continue

            return structured_data

        except Exception as e:
            print(f"读取扫描数据错误: {str(e)}")
            # 查询仪器错误详情
            print("仪器错误状态:", self.kei2410.query(":SYST:ERR?"))
            return []


    def filterVoltageCurrent(self,structured_data, output_format='dict'):
        """
           过滤结构化数据，仅保留电压电流信息

           参数:
               structured_data: 原始数据集(list of dicts)
               output_format: 输出格式 ('dict' 或 'tuple')

           返回:
               根据格式要求返回:
               - 'dict': [{'voltage':v1, 'current':c1}, ...]
               - 'tuple': [(v1, c1), (v2, c2), ...]
           """
        filtered_data = []

        for data_point in structured_data:
            try:
                # 提取电压电流数值
                v = data_point['voltage']
                i = data_point['current']

                # 数值有效性检查
                if not (isinstance(v, (int, float)) and isinstance(i, (int, float))):
                    raise ValueError("电压/电流值类型错误")

                # 按指定格式存储
                if output_format.lower() == 'dict':
                    filtered_data.append({'voltage': v, 'current': i})
                elif output_format.lower() == 'tuple':
                    filtered_data.append((v, i))
                else:
                    raise ValueError("不支持的输出格式，可选 'dict' 或 'tuple'")

            except KeyError as ke:
                print(f"数据点缺失关键字段: {str(ke)}")
            except ValueError as ve:
                print(f"数值错误: {str(ve)}")

        return filtered_data


    ############################# 测量滤波等东西 #################################

    def filter_on(self, count=20, mode="repeat"):               #启用测量滤波
        self.kei2410.write(":sense:average:count " + str(count))#平均次数
        self.kei2410.write(":sense:average:tcontrol " + mode)   # repeat or moving 滤波模式
        self.kei2410.write(":sense:average:state on")

    def filter_off(self):                                       #关闭测量滤波
        self.kei2410.write(":sense:average:state off")

    def __del__(self):                                          #析构函数，关闭仪器连接
        self.kei2410.close()


if __name__ == "__main__":
    kei2410 = keithley2410("ASRL7::INSTR")
    # kei2410 = keithley2410('GPIB0::08::INSTR')
    kei2410.testIO()
