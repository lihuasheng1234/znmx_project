import os
import shutil
import threading
import time
import datetime
import json
import signal
from math import sqrt, log
import random

import numpy as np
import requests
import pandas as pd

import settings


class ProcessFile(threading.Thread):
    def __init__(self, machine_name, machineInfo_input_path, vibrationData_input_path, using_tool_input_path,
                 vibrationData_move_path, result_output_path):
        super().__init__()
        self.machine_name = machine_name

        self.machineInfo_input_path = machineInfo_input_path
        self.vibrationData_input_path = vibrationData_input_path
        self.using_tool_input_path = using_tool_input_path
        self.vibrationData_move_path = vibrationData_move_path
        self.virbation_raw_output_path = os.path.join(result_output_path, settings.VIRBATION_OUTPUT_PATH_NAME)
        self.load_data_output_path = os.path.join(result_output_path, settings.LOAD_DATA_OUTPUT_PATH_NAME)
        self.vibration_rms_output_path = os.path.join(result_output_path, settings.VIRBATION_RMS_OUTPUT_PATH_NAME)
        self.old_tool = 0
        self.usingTool = 0
        self.last_trans_time = self.now
        self.checkPathOrCreate(self.vibrationData_move_path)
        self.checkPathOrCreate(self.virbation_raw_output_path)
        self.checkPathOrCreate(self.load_data_output_path)
        self.checkPathOrCreate(self.vibration_rms_output_path)

        self.hasChangeTool = False
        self.old_vib_data = ""
        self.old_vib_data_count = 0

    def setToolInfo(self):
        """
        获取当前机台加工刀具信息
        :param path:
        :return:
        """

        if not os.path.exists(self.using_tool_input_path):
            print("当前机台加工刀具信息无法确认")
            return False
        path = self.using_tool_input_path

        file_list = os.listdir(path)
        try:
            if file_list:
                tool_info_file = file_list[0]
                temp = tool_info_file.rsplit("-", 1)
                str_time = temp[0]
                tool_name = temp[1].rsplit(".")[0]

                if tool_name == "0" or tool_name == "None":
                    # 说明当前机台正在换刀或者待机中
                    self.usingTool = 0
                    return False
                if not self.usingTool:
                    self.usingTool = tool_name
                elif tool_name != self.usingTool:
                    print("刀具更换:%s->>%s" % (self.usingTool, tool_name))
                    self.old_tool = self.usingTool
                    self.usingTool = tool_name
                    self.hasChangeTool = True

                else:
                    self.hasChangeTool = False
                return True
            else:
                print("路径%s没有文件" % path)
                return False
        except Exception:
            print("机台信息获取失败")

    @staticmethod
    def findLastBeforTime(str_time, files_path=None, p1='%Y-%m-%d-%H-%M-%S-%f', p2='%Y-%m-%d-%H-%M-%S-%f'):
        """
        在files_path中寻找一个文件，这个文件名表示的时间需要比str_time小并且最接近str_time
        算法思路:
            1. 获取路径下所有文件列表 并排序
            2. 把str_time转换为可以比较的形式compile_time
            3. 遍历排序后的列表，其每个元素与compile_time进行一一对比
                1. 如果元素比str_time小继续循环
                2. 如果元素比str_time大：
                    1. 如果元素是第一个元素 则返回-1
                    2. 否则返回上一个元素
            4. 如果遍历完成后还没有返回 则说明所有元素都比compile_time小 即返回列表下最后一个文件
        :param str_time: 要进行比较的时间 2020-12-12-10-07-26-935
        :param files_path: 要寻找的文件夹 2020-12-12-10-07-26-935
        :param p: 时间解析格式如
        :return:  返回最接近并且比时间str_time小的时间为文件名的文件
        """
        # 把str_time转化为可以比较的形式
        try:
            compile_t = datetime.datetime.strptime(str_time, p1)
        except Exception:
            print("需要对比的时间：%s不能被格式：%s所解析，请检查解析格式是否正确" % (str_time, p1))
            return -1
        t_list = os.listdir(files_path)
        if t_list:
            try:
                t_list.sort(key=lambda x: datetime.datetime.strptime(x.split(".")[0], p2))
            except Exception:
                print("路径下：%s文件不能被格式：%s所解析，请检查解析格式是否正确" % (files_path, p1))
            for i, tm in enumerate(t_list):
                # 获得文件所表示的时间字符串并且转换为可以比较的类型
                tm = os.path.splitext(tm)[0]
                t = datetime.datetime.strptime(tm, p2)
                if t > compile_t:
                    return t_list[i - 1] if i != 0 else -1
            return t_list[-1]
        else:
            print("路径：%s下不存在文件" % files_path)

    @staticmethod
    def findLastAfterTime(str_time, files_path=None, p1='%Y-%m-%d-%H-%M-%S-%f', p2='%Y-%m-%d-%H-%M-%S-%f'):
        """
        在files_path中寻找一个文件，这个文件名表示的时间需要比str_time大并且最接近str_time
        算法思路:
            1. 获取路径下所有文件列表 并排序
            2. 把str_time转换为可以比较的形式compile_time
            3. 遍历排序后的列表，其每个元素与compile_time进行一一对比
                1. 如果元素比str_time小继续循环
                2. 如果元素比str_time大直接返回
            4. 如果遍历完成后还没有返回 则说明所有元素都比compile_time小 即返回列表下最后一个文件
        :param str_time: 要进行比较的时间 2020-12-12-10-07-26-935
        :param files_path: 要寻找的文件夹 2020-12-12-10-07-26-935
        :param p1: 时间str_time的解析格式如
        :param p2: 文件路径files_path下文件名的时间解析格式如
        :return:  返回最接近并且比时间str_time小的时间为文件名的文件
        """
        # 把str_time转化为可以比较的形式
        try:
            compile_t = datetime.datetime.strptime(str_time, p1)
        except Exception:
            print("需要对比的时间：%s不能被格式：%s所解析，请检查解析格式是否正确" % (str_time, p1))
            return -1
        t_list = os.listdir(files_path)
        if t_list:
            try:
                t_list.sort(key=lambda x: datetime.datetime.strptime(x.split(".")[0], p2))
            except Exception:
                print("路径下：%s文件不能被格式：%s所解析，请检查解析格式是否正确" % (files_path, p1))
            for i, tm in enumerate(t_list):
                # 获得文件所表示的时间字符串并且转换为可以比较的类型
                tm = os.path.splitext(tm)[0]
                t = datetime.datetime.strptime(tm, p2)
                if t > compile_t:
                    return t_list[i]
            return t_list[-1]
        else:
            print("路径：%s下不存在文件" % files_path)

    @staticmethod
    def checkPathOrCreate(path):
        if os.path.exists(path):
            print("路径已存在->%s" % path)
        else:
            print("创建路径:%s" % path)
            os.makedirs(path, exist_ok=True)

    @staticmethod
    def moveFilesTo(start_file, end_file, src, dest, p='%Y-%m-%d-%H-%M-%S-%f'):
        """
        移动范围内文件到指定目录
        :param start_file: src下开始移动的文件名
        :param end_file: src下结束移动的文件名
        :param src: 源文件地址
        :param dest: 目的地址
        :return:
        """
        t1 = time.time()
        file_list = os.listdir(src)
        if not file_list:
            print("源文件路径[%s]为空" % src)
            return -1

        file_list.sort(key=lambda x: datetime.datetime.strptime(x.split(".")[0], p))
        start = file_list.index(start_file)
        end = file_list.index(end_file)
        for file in file_list[start:end + 1]:
            file_path = os.path.join(src, file)
            shutil.copy(file_path, dest)
        print("移动文件耗时:%s" % (time.time() - t1))

    @property
    def now(self):
        return datetime.datetime.now()

    @property
    def machineTool_output_path(self):
        """
        振动数据分类路径
        :return:
        """
        return os.path.join(self.vibrationData_move_path, self.usingTool)

    @property
    def machineOldTool_output_path(self):
        """
        振动数据分类路径
        :return:
        """
        return os.path.join(self.vibrationData_move_path, self.old_tool)

    @staticmethod
    def date_to_str(date):
        return date.strftime('%Y-%m-%d-%H-%M-%S-%f')[:-3]

    def process_vibrationData(self):
        """
        把振动数据进行变换处理

        :param file_path:  分类收振动数据存放文件路径
        :param tools_num:  当前加工刀具
        :return:
        """
        data = []
        filenames = os.listdir(self.machineTool_output_path)
        filenames.sort(key=lambda x: datetime.datetime.strptime(x.split(".")[0], settings.VIBRATION_FILENAME_PATTERN))
        if len(filenames) < 60:
            print("路径->%s下文件数目不够" % self.machineTool_output_path)
        else:
            count = 0
            for filename in filenames[::-1]:
                if count > 60:
                    break
                data_file_path = os.path.join(self.machineTool_output_path, filename)
                with open(data_file_path, 'r') as f:
                    line = f.readline()
                    if line.endswith(","):
                        line = line[:-1]
                    if line:
                        # curLine = [x for x in line.strip().split(",") if x]
                        curLine = line.strip().split(",")
                        try:
                            fline = np.array(list(map(int, curLine)))
                        except Exception as e:
                            print(e)
                            print("文件内容有误:%s" % data_file_path)
                        tem = sqrt(np.sum(fline ** 2) / len(fline))
                        data.append(tem)
                        count += 1
            # 不够60 补齐至60个数据 极端情况下可能出现不足60个：如果文件存在但是没有内容
            for _ in range(60 - len(data)):
                data.append(data[-1])

            data = np.array(data[::-1])
            data = 1 / (1 + log(data.mean(), 10e12))
            d = dict(data=data)
            # en_json = json.dumps(d, ensure_ascii=True)
            now_str = self.now.strftime(settings.OUTPUT_FILENAME_PATTERN)
            tool_name = str(self.usingTool)
            if len(tool_name) == 1:
                tool_name = "T0" + tool_name
            else:
                tool_name = "T" + tool_name
            output_file_name = "%s-%s.json" % (tool_name, now_str)
            file_path = os.path.join(self.vibration_rms_output_path, output_file_name)
            with open(file_path, 'w') as f:
                json.dump(dict(data=data), f)

    def reduce_vibrationData_fre(self):
        """
        降频振动数据原始值 把震动数据处理后移动到指定路径下
        只读取路径下最新生成的文件
        :return: Json数据文件
        """
        file_list = os.listdir(self.vibrationData_input_path)
        file_list.sort(key=lambda x: datetime.datetime.strptime(x.split(".")[0], settings.VIBRATION_FILENAME_PATTERN))
        if file_list:
            data_path = os.path.join(self.vibrationData_input_path, file_list[-1])
            if self.machine_name == "0002":
                # print(data_path)
                pass
            with open(data_path, 'r') as f:
                line = f.readline()
                if line:
                    curLine = line.strip().split(",")

                    data = list(map(int, curLine[0:60]))

                    now_str = self.now.strftime(settings.OUTPUT_FILENAME_PATTERN)
                    output_file_name = "%s.json" % now_str
                    file_path = os.path.join(self.virbation_raw_output_path, output_file_name)
                    with open(file_path, 'w') as f:
                        json.dump(dict(data=data), f)
            self.old_vib_data = file_list[-1]
        else:
            print("路径：%s下不存在文件" % self.vibrationData_input_path)

    def process_machineData(self):
        file_list = os.listdir(self.machineInfo_input_path)
        if file_list:
            data_path = os.path.join(self.machineInfo_input_path, file_list[-2])
            # 可能由于文件读取xlsx文件是文件正在创建过程中导致无法正确读取而报错
            try:
                df = pd.read_csv(data_path, header=None)
            except Exception as e:
                print(e)
                return
            data = np.array(df.iloc[:, 2]).tolist()
            now_str = self.now.strftime(settings.OUTPUT_FILENAME_PATTERN)
            output_file_name = "%s.json" % now_str
            file_path = os.path.join(self.load_data_output_path, output_file_name)
            with open(file_path, 'w') as f:
                json.dump(dict(data=data), f)

        pass

    def run(self) -> None:
        """
        算法本体
        算法每隔60s运行一次指定算法程序来处理振动数据得到变换后的振动数据
        算法每隔1s运行一次指定算法程序来处理振动数据得到降频振动数据
        算法每隔1s运行一次指定算法程序来处理机台信息得到负载信息
        :return:
        """

        while 1:

            while True:
                self.reduce_vibrationData_fre()
                self.process_machineData()
                time.sleep(1)

                if not self.setToolInfo():
                    print("获取机台信息失败")
                    break
                last_trans_time_str = self.date_to_str(self.last_trans_time)
                now_str = self.date_to_str(self.now)
                print("%s->上次传输数据时间:%s, 当前时间:%s, 当前加工刀具:%s" % (
                    self.machine_name, last_trans_time_str, now_str, self.usingTool))
                if (self.now - self.last_trans_time).seconds >= 60 and self.usingTool != 0:
                    first_vib_file = self.findLastAfterTime(last_trans_time_str,
                                                            files_path=self.vibrationData_input_path,
                                                            p1="%Y-%m-%d-%H-%M-%S-%f",
                                                            p2=settings.VIBRATION_FILENAME_PATTERN)
                    last_vib_file = self.findLastBeforTime(now_str, files_path=self.vibrationData_input_path)
                    self.checkPathOrCreate(self.machineTool_output_path)
                    self.last_trans_time = self.now
                    self.moveFilesTo(first_vib_file, last_vib_file, self.vibrationData_input_path,
                                     self.machineTool_output_path)

                    t1 = time.time()
                    self.process_vibrationData()
                    print("处理完成时间：%s" % (time.time() - t1))
                # 如果换刀了 需要移动
                if self.hasChangeTool:
                    first_vib_file = self.findLastAfterTime(last_trans_time_str,
                                                            files_path=self.vibrationData_input_path,
                                                            p1="%Y-%m-%d-%H-%M-%S-%f",
                                                            p2=settings.VIBRATION_FILENAME_PATTERN)
                    last_vib_file = self.findLastBeforTime(now_str, files_path=self.vibrationData_input_path,
                                                           p1="%Y-%m-%d-%H-%M-%S-%f",
                                                           p2=settings.VIBRATION_FILENAME_PATTERN
                                                           )
                    self.checkPathOrCreate(self.machineOldTool_output_path)
                    self.last_trans_time = self.now
                    self.moveFilesTo(first_vib_file, last_vib_file, self.vibrationData_input_path,
                                     self.machineOldTool_output_path)


if __name__ == '__main__':
    try:

        t_list = []
        for machine in settings.MACHINE_SETTINGS:
            t_list.append(
                ProcessFile(machine_name=machine["param"], machineInfo_input_path=machine["MachineData_INPUT_PATH"],
                            vibrationData_input_path=machine["SensorData_INPUT_PATH"],
                            using_tool_input_path=machine['ToolInfo_INPUT_PATH'],
                            vibrationData_move_path=machine["SensorData_MOVE_PATH"],
                            result_output_path=machine["Result_OUPUT_PATH"]))

        for t in t_list:
            t.start()
        for t in t_list:
            t.join()
    except Exception as e:
        print(e)
