"""
Author:Shiyue Wang
Control_Keithley2430.py
"""
import pyvisa
import time
import warnings
import pandas as pd
import os
import numpy

class keithley2430:
    def __init__(self, resource_name):                          #初始化函数，建立与仪器的连接输入 'GPIB0::08::INSTR'
        self.instlist = pyvisa.ResourceManager()
        self.kei2430 = self.instlist.open_resource(resource_name)    #打开keithley2430的仪器资源（.open_resource('GPIB0::08::INSTR')）f"ASRL3::INSTR"
        self.kei2430.baud_rate = 19200
        self.kei2430.data_bits = 8
        self.kei2430.stop_bits = pyvisa.constants.StopBits.one
        self.kei2430.parity = pyvisa.constants.Parity.none
        self.kei2430.flow_control = pyvisa.constants.ControlFlow.none
        # my_instrument.flow_control = visa.constants.ControlFlow.rts_cts
        self.kei2430.read_termination = '\r'
        self.kei2430.write_termination = '\r'
        self.kei2430.timeout = 5000  # 单位毫秒
        self.kei2430.write('*RST')
        time.sleep(2)  # 等待复位完成
        self.outputOff()  # 确保输出关闭
        self.sourceVDataBase = pd.DataFrame(columns=["TimeStamp", "Voltage(V)", "Current(A)", "Resistor(Ohm)"]) # 建立电压源模式数据容器
        self.sourceIDataBase = pd.DataFrame(columns=["TimeStamp", "Current(A)", "Voltage(V)"])
        self.kei2430.timeout = 25000                            #设置超时时间为25s
        self.globalCurrentProtection = '105E-6'  # global current protection       #设置全局电流保护值默认值105uA

    ##########################################################基本功能函数############################################################

    def safe_initialize(self):
        try:
            self.outputOff()
            self.setCurrentProtection(105e-6)
            self.directSetVoltageOutput(0)
        except Exception as e:
            print(f"2430 初始化安全措施失败: {str(e)}")

    def testIO(self):                                           #测试仪器通信
        message = self.kei2430.query('*IDN?')                   #正常会返回：KEITHLEY INSTRUMENTS INC.,MODEL 2430,1056236,C27   Feb  4 2004 14:58:04/A02  /D/H
        print(message)

    def outputOn(self):                                        #启用输出
        self.kei2430.write(":output on")
        print("2430 Output on")

    def outputOff(self):                                       #停止输出
        self.kei2430.write(":output off")
        print("2430 Output off")

    def get_output_state(self):
        """获取当前输出状态"""
        return self.kei2430.query(":OUTPUT?").strip() == '1'

    def directSetVoltageOutput(self, vol):
        self.kei2430.write(":source:voltage:level "+str(vol))

    def directSetCurrentOutput(self, curr):
        self.kei2430.write(":source:current:level " + str(curr))

    def showVoltage(self):                                     #读取当前电压值
        data = self.kei2430.query(":read?").split(',')
        voltage = data[0]
        print("2430 voltage [V]: " + str(voltage))
        return float(voltage)

    def showCurrent(self):                                     #读取当前电压值
        data = self.kei2430.query(":read?").split(',')
        current = data[1]
        print("2430 current [A]: " + str(current))
        return float(current)

    def beep(self, freq=1046.50, duration=0.3):                 #发出提示音
        self.kei2430.write(":system:beeper " + str(freq) + ", " + str(duration))
        time.sleep(duration)

    def resetInstruments(self):
        self.kei2430.write('*RST')
        time.sleep(0.1)  # 等待复位完成

    ##########################################################读写存储相关函数############################################################
    def saveCurrentSweepData(self, filename="Log_SweepData.xlsx"):
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
                                  for sheet in excel.sheet_names if sheet != '2430Current'}
                except Exception as e:
                    print(f"读取现有文件时发生警告: {str(e)}")

            # 使用openpyxl引擎写入数据（支持.xlsx格式）
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # 保留原有工作表（排除Current）
                for sheet_name, data in sheets.items():
                    data.to_excel(writer, sheet_name=sheet_name, index=False)
                # 写入当前数据到Current工作表
                df.to_excel(writer, sheet_name='2430Current', index=False)

            print(f"扫描数据已成功保存至 {filename} 的 [2430Current] 工作表")

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
                                  for sheet in excel.sheet_names if sheet != '2430Voltage'}
                except Exception as e:
                    print(f"读取现有文件时发生警告: {str(e)}")

            # 使用openpyxl引擎写入数据（支持.xlsx格式）
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # 保留原有工作表（排除Current）
                for sheet_name, data in sheets.items():
                    data.to_excel(writer, sheet_name=sheet_name, index=False)
                # 写入当前数据到Current工作表
                df.to_excel(writer, sheet_name='2430Voltage', index=False)

            print(f"扫描数据已成功保存至 {filename} 的 [2430Voltage] 工作表")

        except PermissionError:
            print("错误：文件被占用，请关闭Excel后重试")
        except Exception as e:
            print(f"保存过程中发生错误: {str(e)}")

    def savePulseData(self, sheetname='IPulse', filename="Log_PulseData.xlsx"):
        """保存扫描数据到Excel文件的工作表中"""
        try:
            # 读取扫描数据
            structured_data = self.readPulseData()
            if not structured_data:
                print("无扫描数据可保存")
                return

            # 将嵌套数据结构转换为平面DataFrame
            df = pd.json_normalize(structured_data, sep='_')

            # 添加系统时间戳（整个保存操作的时间）
            df.insert(0, "Save_Timestamp", pd.Timestamp.now())

            # 读取所有现有工作表数据（如果文件存在）
            all_sheets = {}
            if os.path.isfile(filename):
                try:
                    with pd.ExcelFile(filename) as excel:
                        # 读取所有工作表
                        all_sheets = {sheet: pd.read_excel(excel, sheet_name=sheet)
                                      for sheet in excel.sheet_names}
                except Exception as e:
                    print(f"读取现有文件时警告: {str(e)}")

            # 更新目标工作表数据（完全覆盖）
            all_sheets[sheetname] = df  # 直接替换，不保留旧数据

            # 写入整个文件（模式用'w'确保完全覆盖）
            with pd.ExcelWriter(
                    filename,
                    engine='openpyxl',
                    mode='w'  # 始终使用写入模式，因为我们已经读取了所有需要保留的数据
            ) as writer:
                for sheet_name, data in all_sheets.items():
                    data.to_excel(writer, sheet_name=sheet_name, index=False)

            print(f"数据已成功保存至 {filename} 的 {sheetname} 工作表")

        except PermissionError:
            print("错误：文件被占用，请关闭Excel后重试")
        except Exception as e:
            print(f"保存过程中发生错误: {str(e)}")



    ##########################################################电压源模式相关函数############################################################
    def setSourceVoltage(self):
        self.kei2430.write(":source:function voltage")
        self.kei2430.write(":sense:function 'current'")
    def setCurrentProtection(self, current):                  #设置电流保护阈值
        self.globalCurrentProtection = str(current)
        self.kei2430.write(":sense:current:protection " + str(current))

    ##########################################################电流源模式相关函数############################################################
    def setSourceCurrent(self):
        self.kei2430.write(":source:function current")
        self.kei2430.write(":sense:function 'voltage'")

    def display_current(self):                                  #显示当前电流值
        self.kei2430.write(":sense:function 'current'")
        self.kei2430.write(":sense:current:range:auto on")      #自动量程
        self.kei2430.write(":display:enable on")                #启用显示屏
        self.kei2430.write(":display:digits 7")                 #显示7位数字
        self.kei2430.write(":form:elem current")                #返回格式仅电流
        current = self.kei2430.query(":read?")
        print("2430 current [A]: " + str(current))
        return float(str(current))

    def setVoltageProtection(self, vol):                      #设置电压量程保护
        self.kei2430.write(":sense:voltage:protection " + str(vol))


    ##########################################################扫描模式相关函数#########################################################
    def CurrentSweep(self, sweep_type='linear', start=1e-3, stop=10e-3, step=1e-3, point=5, compliance=10, delay=0.5):
        self.kei2430.write(":TRAC:POIN 1000")  # 设置缓冲区大小
        self.kei2430.write(":TRAC:CLE")  # 清空缓冲区
        self.kei2430.write(":TRAC:FEED SENS")  # 存储测量数据
        if sweep_type == 'linear':
            # 计算扫描点数
            count = int((stop-start)/step) + 1
            # self.kei2430.write("*RST")
            self.kei2430.write(":sense:function:CONC OFF")
            self.kei2430.write(":source:function current")
            self.kei2430.write(":sense:function 'VOlT:DC'")
            self.kei2430.write(":sense:voltage:protection " + str(compliance))
            self.kei2430.write(":source:current:start " + str(start))
            self.kei2430.write(":source:current:stop " + str(stop))
            self.kei2430.write(":source:current:step " + str(step))
            self.kei2430.write(":source:current:mode sweep")
            self.kei2430.write(":SOUR:SWE:RANG AUTO")
            self.kei2430.write(":source:sweep:SPAC LIN")
            self.kei2430.write(":TRIG:COUN " + str(count))
            self.kei2430.write(":source:delay " + str(delay))
            self.kei2430.write(":OUTP ON")
            self.kei2430.write(":READ?")
        else:
            # self.kei2430.write("*RST")
            self.kei2430.write(":sense:function:CONC OFF")
            self.kei2430.write(":source:function current")
            self.kei2430.write(":sense:function 'VOlT:DC'")
            self.kei2430.write(":sense:voltage:protection " + str(compliance))
            self.kei2430.write(":source:current:start " + str(start))
            self.kei2430.write(":source:current:stop " + str(stop))
            self.kei2430.write(":source:current:mode sweep")
            self.kei2430.write(":SOUR:SWE:RANG AUTO")
            self.kei2430.write(":source:sweep:SPAC LOG")
            self.kei2430.write(":source:sweep:POINts " + str(point))
            self.kei2430.write(":TRIG:COUN " + str(point))
            self.kei2430.write(":source:delay " + str(delay))
            self.kei2430.write(":OUTP ON")
            self.kei2430.write(":READ?")
        # self.kei2430.query("*OPC?")  # 阻塞直到操作完成
        # data = self.kei2430.read()
        # print(data)

    def VoltageSweep(self, sweep_type='linear', start=1, stop=10, step=1, point=5, compliance=12e-3, delay=0.5):
        self.kei2430.write(":TRAC:POIN 1000")  # 设置缓冲区大小
        self.kei2430.write(":TRAC:CLE")  # 清空缓冲区
        self.kei2430.write(":TRAC:FEED SENS")  # 存储测量数据
        if sweep_type == 'linear':
            # 计算扫描点数
            count = int((stop-start)/step) + 1
            # self.kei2430.write("*RST")
            self.kei2430.write(":sense:function:CONC OFF")
            self.kei2430.write(":source:function voltage")
            self.kei2430.write(":sense:function 'CURRENT:DC'")
            self.kei2430.write(":sense:current:protection " + str(compliance))
            self.kei2430.write(":source:voltage:start " + str(start))
            self.kei2430.write(":source:voltage:stop " + str(stop))
            self.kei2430.write(":source:voltage:step " + str(step))
            self.kei2430.write(":source:voltage:mode sweep")
            self.kei2430.write(":SOUR:SWE:RANG AUTO")
            self.kei2430.write(":source:sweep:SPAC LIN")
            self.kei2430.write(":TRIG:COUN " + str(count))
            self.kei2430.write(":source:delay " + str(delay))
            self.kei2430.write(":OUTP ON")
            self.kei2430.write(":READ?")
        else:
            # self.kei2430.write("*RST")
            self.kei2430.write(":sense:function:CONC OFF")
            self.kei2430.write(":source:function voltage")
            self.kei2430.write(":sense:function 'CURRENT:DC'")
            self.kei2430.write(":sense:current:protection " + str(compliance))
            self.kei2430.write(":source:voltage:start " + str(start))
            self.kei2430.write(":source:voltage:stop " + str(stop))
            self.kei2430.write(":source:voltage:mode sweep")
            self.kei2430.write(":SOUR:SWE:RANG AUTO")
            self.kei2430.write(":source:sweep:SPAC LOG")
            self.kei2430.write(":source:sweep:POINts " + str(point))
            self.kei2430.write(":TRIG:COUN " + str(point))
            self.kei2430.write(":source:delay " + str(delay))
            self.kei2430.write(":OUTP ON")
            self.kei2430.write(":READ?")
        # self.kei2430.query("*OPC?")  # 阻塞直到操作完成 加上对read产生重大打击
        # data = self.kei2430.read()    # read测试用
        # print(data)

    def readSweepData(self):
        """读取当前扫描数据，返回结构化数据"""
        try:
            # 读取原始数据字符串（自动触发仪器发送缓存数据）
            raw_data = self.kei2430.read()
            print(raw_data)
            # 分割分号，只保留数据部分（部分仪器会在末尾添加";1"表示结束）
            if ';' in raw_data:
                raw_data = raw_data.split(';')[0]
            # 按逗号分割数据（数据格式：电压,电流,电阻,时间,状态）
            data_points = raw_data.strip().split(',')
            self.kei2430.write(":OUTP OFF")
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
            print("仪器错误状态:", self.kei2430.query(":SYST:ERR?"))
            return []

    def filterVoltageCurrent(self, structured_data, output_format='dict'):
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
    ##########################################################脉冲模式相关函数#########################################################

    def PulseMode2430(self, PulseWidth=0.002, Delay=0.1, ArmCount=2, TriggerCount=5, SourceMode='current', HighLevel=0.001, CurrentProtection=10, VoltageProtection=20):
        print("PulseMode2430ing")

        self.kei2430.write(":TRAC:POIN 1000")  # 设置缓冲区大小
        self.kei2430.write(":TRAC:CLE")  # 清空缓冲区
        self.kei2430.write(":TRAC:FEED SENS")  # 存储测量数据

        self.kei2430.write(':SOUR:FUNC:SHAPE PULSE')  # 进入脉冲模式
        self.kei2430.write(':SOUR:PULS:WIDT ' + str(PulseWidth))  # 2ms脉冲宽度（注意10A量程限制2.5ms）
        self.kei2430.write(':SOUR:PULS:DEL ' + str(Delay))  # 100ms延迟
        # 设置触发系统
        self.kei2430.write(':ARM:SOUR IMM')  # 设置Arm触发源为立即触发
        self.kei2430.write(':ARM:COUN ' + str(ArmCount))  # 臂计数=2（与面板示例对应）
        self.kei2430.write(':TRIG:COUN ' + str(TriggerCount))  # 触发计数=5（总脉冲数=2x5=10）
        # 设置源系统
        if SourceMode == 'current':
            self.kei2430.write(":source:function current")
            self.kei2430.write(":sense:function 'voltage'")
            self.kei2430.write(':SOURce:current:LEVEL ' + str(HighLevel))  # 设置输出电流1mA
            self.kei2430.write(':SENS:VOLT:PROT ' + str(VoltageProtection))  # 电压合规保护20V
        else:
            self.kei2430.write(":source:function voltage")
            self.kei2430.write(":sense:function 'current'")
            self.kei2430.write(':SOURce:voltage:LEVEL ' + str(HighLevel))  # 设置输出电压
            self.kei2430.write(':SENS:CURR:PROT ' + str(CurrentProtection))  # 电流合规保护10A
        # 设置测量系统
        # 设置脉冲测量速度（对应Set pulse speed章节）
        self.kei2430.write(':SENS:VOLT:NPLC 0.004')  # 设置0.01 NPLC（对应面板速度设置） 最快设置为0.004
        # 禁用自动归零（对应Disable auto zero章节）
        self.kei2430.write(':SYST:AZER:STAT OFF')  # 关闭自动归零提升速度
        # 启用脉冲输出（面板操作最后步骤）
        self.kei2430.write(':OUTP ON')
        # # ========== 数据采集 ==========
        self.kei2430.write(":READ?")
        # time.sleep(3)
        print("pulse end")
        # raw_data = self.kei2430.read()
        # print(raw_data)

    def readPulseData(self):
        """读取当前扫描数据，返回结构化数据"""
        time.sleep(5)
        try:
            # 读取原始数据字符串（自动触发仪器发送缓存数据）
            raw_data = self.kei2430.read()
            # 按逗号分割数据（数据格式：电压,电流,电阻,时间,状态）
            data_points = raw_data.strip().split(',')
            self.kei2430.write(":OUTP OFF")
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
            print("仪器错误状态:", self.kei2430.query(":SYST:ERR?"))
            return []

##########################################################脉冲扫描模式相关函数#########################################################

    def PulseSweepMode2430(self, PulseWidth=0.005, Delay=0.003, SourceMode='voltage', StartLevel=1, StopLevel=5, StepLevel=1, CurrentProtection=10, VoltageProtection=20):

        print("PulseSweepMode2430ing")

        self.kei2430.write(":TRAC:POIN 1000")  # 设置缓冲区大小
        self.kei2430.write(":TRAC:CLE")  # 清空缓冲区
        self.kei2430.write(":TRAC:FEED SENS")  # 存储测量数据

        self.kei2430.write(':SOUR:FUNC:SHAPE PULSE')  # 进入脉冲模式
        self.kei2430.write(':SOUR:PULS:WIDT ' + str(PulseWidth))  # 5ms脉冲宽度
        self.kei2430.write(':SOUR:PULS:DEL ' + str(Delay))  # 3ms延迟

        self.kei2430.write('sense:voltage:NPLC 0.01')
        # 设置触发系统
        TriggerCount = int(abs(StopLevel - StartLevel) / abs(StepLevel)) + 1
        print(TriggerCount)
        self.kei2430.write(':TRIG:COUN ' + str(TriggerCount))  # 触发计数=5（总脉冲数=2x5=10）
        # 设置源系统
        if SourceMode == 'current':
            print("current")
            self.kei2430.write(":source:function current")
            self.kei2430.write(":sense:function 'voltage'")
            self.kei2430.write(':SENS:VOLT:PROT ' + str(VoltageProtection))  # 电流合规保护10A
            self.kei2430.write(':source:current:start ' + str(StartLevel))
            self.kei2430.write(':source:current:stop ' + str(StopLevel))
            self.kei2430.write(':source:current:step ' + str(StepLevel))
            self.kei2430.write(':source:current:mode sweep')
        else:
            print("voltage")
            self.kei2430.write(":source:function voltage")
            self.kei2430.write(":sense:function 'current'")
            self.kei2430.write(':SENS:CURR:PROT ' + str(CurrentProtection))  # 电流合规保护10A
            self.kei2430.write(':source:VOLT:start ' + str(StartLevel))
            self.kei2430.write(':source:VOLT:stop ' + str(StopLevel))
            self.kei2430.write(':source:VOLT:step ' + str(StepLevel))
            self.kei2430.write(':source:VOLT:mode sweep')

        # 设置测量系统
        # 设置脉冲测量速度（对应Set pulse speed章节）
        # self.kei2430.write(':SENS:VOLT:NPLC 0.01')  # 设置0.01 NPLC（对应面板速度设置） 最快设置为0.004
        # 禁用自动归零（对应Disable auto zero章节）
        # self.kei2430.write(':SYST:AZER:STAT OFF')  # 关闭自动归零提升速度
        # # 启用脉冲输出（面板操作最后步骤）
        # self.kei2430.write(':OUTP ON')
        # # ========== 数据采集 ==========
        self.kei2430.write(":READ?")

        print("pulse end")
        time.sleep(3)
        # raw_data = self.kei2430.read()
        # print(raw_data)



if __name__ == "__main__":
    kei2430 = keithley2430("ASRL3::INSTR")
    # kei2430 = keithley2430('GPIB0::08::INSTR')
    kei2430.testIO()