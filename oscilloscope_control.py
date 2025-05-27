"""""""""""""""""""""""""""""""""
控制示波器的函数


"""""""""""""""""""""""""""""""""
import pyvisa as visa

class MDO44:
    def __init__(self, resource_name):
        rm = visa.ResourceManager()
        # rm.list_resources()
        print(rm.list_resources())
        self.generator = rm.open_resource(resource_name)  # 信号发生器地址为10  'GPIB0::10::INSTR'
        print("厂家、型号、序列号、固件版本为：")
        print(self.generator.query('*IDN?'))

    def testIO(self):                                           #测试仪器通信
        message = self.MDO.query('*IDN?')                   #正常会返回：KEITHLEY INSTRUMENTS INC.,MODEL 2410,4406455,C34 Sep 21 2016 15:30:00/A02  /L/M
        print(message)


if __name__ == "__main__":
    MDO = MDO44('GPIB0::11::INSTR')
    MDO.testIO()







