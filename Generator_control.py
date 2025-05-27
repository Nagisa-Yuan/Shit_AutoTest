"""""""""""""""""""""""""""""""""
AFG31102(新）信号发生器地址为10
AFG3102C(老）信号发生器地址为11

"""""""""""""""""""""""""""""""""

import pyvisa as visa

class AFG31102:
    def __init__(self, resource_name):
        rm = visa.ResourceManager()
        rm.list_resources()
        self.generator = rm.open_resource(resource_name)  # 信号发生器地址为10  'GPIB0::10::INSTR'
        # print("厂家、型号、序列号、固件版本为：")
        # print(self.generator.query('*IDN?'))

    def testIO(self):                                           #测试仪器通信
        message = self.generator.query('*IDN?')
        print(message)

    # ******************************************************初始化函数**********************************************************
    # 调节负载阻抗，单位：Ω，数值：1-10,000
    def set_impedance(self, channel, res):
        commands = [
            f"OUTPut{channel}:IMPedance {res}", #调节负载阻抗
        ]
        for cmd in commands:
            self.generator.write(cmd)

    # 设置负载阻抗为高阻（＞10kΩ）
    def set_impedance_highZ(self, channel):
        commands = [
            f"OUTPut{channel}:IMPedance INFinity", #设置负载阻抗为高阻抗
        ]
        for cmd in commands:
            self.generator.write(cmd)

    # 波形反相（0：正常，1：反相）
    def set_reverse(self, channel, flag):
        if flag:
            commands = [
                f"OUTPut{channel}:POLarity INVerted",
            ]
            for cmd in commands:
                self.generator.write(cmd)
        else:
            commands = [
                f"OUTPut{channel}:POLarity NORMal",
            ]
            for cmd in commands:
                self.generator.write(cmd)

    # 复位
    def reset(self):
        self.generator.write('*RST')

    #******************************************************运行模式************************************************************
    # continuous模式
    def setmode_continuous(self, channel):
        commands = [
            f"SOURce{channel}:BURSt:STATe OFF",  # 禁用burst
            f"SOURce{channel}:FREQuency:MODE CW",  # 设为连续波模式
        ]
        for cmd in commands:
            self.generator.write(cmd)

    # burst模式，外部trigger触发
    # N周期数
    # delay延迟时间（ns）（0.0 ns to 85.000 s）
    def setmode_burst_external(self, channel, N, delay):
        commands = [
            f"SOURce{channel}:BURSt:STATe ON",  # 开启burst
            f"SOURce{channel}:BURSt:NCYCles {N}",  # N个周期
            f"SOURce{channel}:BURSt:TDELay {delay}ns",  # 延迟ns
            f"SOURce{channel}:BURSt:MODE TRIGgered",  # 触发模式
            f"TRIGger:SOURce EXTernal",  # 触发源：外部触发
        ]
        for cmd in commands:
            self.generator.write(cmd)


    # # burst模式，内部计时器触发
    # # N周期数
    # # delay延迟时间（ns）（0.0 ns to 85.000 s）
    # # interval间隔时间（μs）（1 μs to 500.0 s）
    # def setmode_burst_internal(self, channel, N, delay, interval):
    #     commands = [
    #         f"SOURce{channel}:BURSt:STATe ON",  # 开启burst
    #         f"SOURce{channel}:BURSt:NCYCles {N}",  # N个周期
    #         f"SOURce{channel}:BURSt:TDELay {delay}ns",  # 延迟ns
    #         f"SOURce{channel}:BURSt:MODE TRIGgered",  # 触发模式
    #         f"TRIGger:SOURce TIMer",  # 触发源：内部定时器触发
    #         f"TRIGger:SOURce TIMer {interval}",  # 设置间隔时间
    #     ]
    #     for cmd in commands:
    #         self.generator.write(cmd)



    # 触发trigger
    def pushtrigger(self):
        commands = [
            f"TRIGger:IMMediate",  # pushtrigger
        ]
        for cmd in commands:
            self.generator.write(cmd)


    #******************************************************波形设置************************************************************


    # 方波
    def setwave_square(self, channel, high, low, freq):
        commands = [
            f"SOURce{channel}:FUNCtion:SHAPe SQUare",  # 设置方波
            f"SOURce{channel}:FREQuency {freq}Hz",  # 设置频率
            f"SOURce{channel}:VOLTage:LEVel:IMMediate:HIGH {high}V",  # 设置高电平
            f"SOURce{channel}:VOLTage:LEVel:IMMediate:LOW {low}V",  # 设置低电平
        ]
        for cmd in commands:
            self.generator.write(cmd)

    # 正弦波
    def setwave_sine(self, channel, high, low, freq):
        commands = [
            f"SOURce{channel}:FUNCtion:SHAPe SINusoid",  # 设置正弦波
            f"SOURce{channel}:FREQuency {freq}Hz",  # 设置频率
            f"SOURce{channel}:VOLTage:LEVel:IMMediate:HIGH {high}V",  # 设置高电平
            f"SOURce{channel}:VOLTage:LEVel:IMMediate:LOW {low}V",  # 设置低电平
        ]
        for cmd in commands:
            self.generator.write(cmd)

    # PWM波
    def setwave_PWM(self, channel, high, low, freq, duty):
        commands = [
            f"SOURce{channel}:FUNCtion:SHAPe PULSe",  # 设置PWM波
            f"SOURce{channel}:FREQuency {freq}Hz",  # 设置频率
            f"SOURce{channel}:VOLTage:LEVel:IMMediate:HIGH {high}V",  # 设置高电平
            f"SOURce{channel}:VOLTage:LEVel:IMMediate:LOW {low}V",  # 设置低电平
            f"SOURce{channel}:PULSe:DCYCle {duty}",  # 设置占空比
        ]
        for cmd in commands:
            self.generator.write(cmd)

    # ******************************************************波形设置************************************************************

    # 开启输出
    def output_on(self, channel):
            self.generator.write(f"OUTPut{channel}:STATE ON")

    # 关闭输出
    def output_off(self, channel):
            self.generator.write(f"OUTPut{channel}:STATE OFF")

class AFG3102C:
    def __init__(self, resource_name):
        rm = visa.ResourceManager()
        rm.list_resources()
        self.generator = rm.open_resource(resource_name)  # 信号发生器地址为11  'GPIB0::11::INSTR'
        print("厂家、型号、序列号、固件版本为：")
        print(self.generator.query('*IDN?'))

    #******************************************************初始化函数**********************************************************
    # 调节负载阻抗
    def set_impedance(self, channel, res):
        commands = [
            f"OUTPut{channel}:IMPedance {res}", #调节负载阻抗
        ]
        for cmd in commands:
            self.generator.write(cmd)

    # 设置负载阻抗为高阻
    def set_impedance_highZ(self, channel):
        commands = [
            f"OUTPut{channel}:IMPedance INFinity", #设置负载阻抗为高阻抗
        ]
        for cmd in commands:
            self.generator.write(cmd)

    # 波形反相（0：正常，1：反相）
    def set_reverse(self, channel, flag):
        if flag:
            commands = [
                f"OUTPut{channel}:POLarity INVerted",
            ]
            for cmd in commands:
                self.generator.write(cmd)
        else:
            commands = [
                f"OUTPut{channel}:POLarity NORMal",
            ]
            for cmd in commands:
                self.generator.write(cmd)

    # 复位
    def reset(self):
        self.generator.write('*RST')

    #******************************************************运行模式************************************************************
    # continuous模式
    def setmode_continuous(self, channel):
        commands = [
            f"SOURce{channel}:BURSt:STATe OFF",  # 禁用burst
            f"SOURce{channel}:FREQuency:MODE CW",  # 设为连续波模式
        ]
        for cmd in commands:
            self.generator.write(cmd)

    # burst模式，外部trigger触发
    # N周期数
    # delay延迟时间（ns）（0.0 ns to 85.000 s）
    def setmode_burst_external(self, channel, N, delay):
        commands = [
            f"SOURce{channel}:BURSt:STATe ON",  # 开启burst
            f"SOURce{channel}:BURSt:NCYCles {N}",  # N个周期
            f"SOURce{channel}:BURSt:TDELay {delay}ns",  # 延迟ns
            f"SOURce{channel}:BURSt:MODE TRIGgered",  # 触发模式
            f"TRIGger:SOURce EXTernal",  # 触发源：外部触发
        ]
        for cmd in commands:
            self.generator.write(cmd)


    # # burst模式，内部计时器触发
    # # N周期数
    # # delay延迟时间（ns）（0.0 ns to 85.000 s）
    # # interval间隔时间（μs）（1 μs to 500.0 s）
    # def setmode_burst_internal(self, channel, N, delay, interval):
    #     commands = [
    #         f"SOURce{channel}:BURSt:STATe ON",  # 开启burst
    #         f"SOURce{channel}:BURSt:NCYCles {N}",  # N个周期
    #         f"SOURce{channel}:BURSt:TDELay {delay}ns",  # 延迟ns
    #         f"SOURce{channel}:BURSt:MODE TRIGgered",  # 触发模式
    #         f"TRIGger:SOURce TIMer",  # 触发源：内部定时器触发
    #         f"TRIGger:SOURce TIMer {interval}",  # 设置间隔时间
    #     ]
    #     for cmd in commands:
    #         self.generator.write(cmd)



    # 触发trigger
    def pushtrigger(self):
        commands = [
            f"TRIGger:IMMediate",  # pushtrigger
        ]
        for cmd in commands:
            self.generator.write(cmd)


    #******************************************************波形设置************************************************************


    # 方波
    def setwave_square(self, channel, high, low, freq):
        commands = [
            f"SOURce{channel}:FUNCtion:SHAPe SQUare",  # 设置方波
            f"SOURce{channel}:FREQuency {freq}Hz",  # 设置频率
            f"SOURce{channel}:VOLTage:LEVel:IMMediate:HIGH {high}V",  # 设置高电平
            f"SOURce{channel}:VOLTage:LEVel:IMMediate:LOW {low}V",  # 设置低电平
        ]
        for cmd in commands:
            self.generator.write(cmd)

    # 正弦波
    def setwave_sine(self, channel, high, low, freq):
        commands = [
            f"SOURce{channel}:FUNCtion:SHAPe SINusoid",  # 设置正弦波
            f"SOURce{channel}:FREQuency {freq}Hz",  # 设置频率
            f"SOURce{channel}:VOLTage:LEVel:IMMediate:HIGH {high}V",  # 设置高电平
            f"SOURce{channel}:VOLTage:LEVel:IMMediate:LOW {low}V",  # 设置低电平
        ]
        for cmd in commands:
            self.generator.write(cmd)

    # PWM波
    def setwave_PWM(self, channel, high, low, freq, duty):
        commands = [
            f"SOURce{channel}:FUNCtion:SHAPe PULSe",  # 设置PWM波
            f"SOURce{channel}:FREQuency {freq}Hz",  # 设置频率
            f"SOURce{channel}:VOLTage:LEVel:IMMediate:HIGH {high}V",  # 设置高电平
            f"SOURce{channel}:VOLTage:LEVel:IMMediate:LOW {low}V",  # 设置低电平
            f"SOURce{channel}:PULSe:DCYCle {duty}",  # 设置占空比
        ]
        for cmd in commands:
            self.generator.write(cmd)

    # ******************************************************波形设置************************************************************

    # 开启输出
    def output_on(self, channel):
            self.generator.write(f"OUTPut{channel}:STATE ON")

    # 关闭输出
    def output_off(self, channel):
            self.generator.write(f"OUTPut{channel}:STATE OFF")




# 单独测试控制函数用的main函数
if __name__ == "__main__":
    AFG1 = AFG31102('GPIB0::11::INSTR')
    AFG1.reset()






#     generator.write('OUTPUT1:STATE ON')  # 开启通道1输出
