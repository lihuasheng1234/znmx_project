from gevent import monkey
monkey.patch_all()

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
import pymongo
import pymysql
import requests
import pandas as pd
from signalr import Connection
from requests import Session

import settings2




class ProcessVibData(threading.Thread):
    def __init__(self, machine_num, tool_num):
        super().__init__()
        self.machine_num = machine_num
        self.ready = False
        self.tool_num = tool_num
        self.last_computed_time = self.now

    def setup(self):
        print("正在准备中。。。")
        self.get_mangodb_connect()
        self.get_mysql_connect()
        self.get_signalr_hub()
        self.ready = True
        pass

    def get_mangodb_connect(self):
        try:
            self.mangodb_connect = pymongo.MongoClient(settings2.mangodb_info['host'], serverSelectionTimeoutMS=settings2.mangodb_info['connect_timeoutMS'])
        except Exception as e:
            print(e)
            self.ready = False

    def get_mysql_connect(self):
        """
        获取上传刀具健康度的mysql连接
        """
        try:
            self.mysql_connect = pymysql.connect(**settings2.hp_mysql_info)
            self.cursor = self.mysql_connect.cursor()
        except Exception as e:
            print(e)
            self.ready = False

    def get_signalr_hub(self):
        try:
            self.session = Session()
            self.connection = Connection("http://202.104.118.59:8070/signalr/", self.session)
            self.hub = self.connection.register_hub('dashBoardHub')
            self.connection.start()
        except Exception as e:
            print(e)
            self.ready = False

    def input_vibration(self):
        """
        输入振动数据
        """

        pass

    def get_vibdata_from_database(self, limit=10):
        '''
        获取振动数据
        return: {'_id': ObjectId('601147a535483a2b907e8670'), 'time': '2021-01-27-18-59-49-562', 'xdata': [400个点], 'ydata': [400个点], 'zdata': [400个点]}
        '''
        cols = self.mangodb_connect["VibrationData"]["Sensor01"].find({}, sort=[('_id', pymongo.DESCENDING)], limit=limit)
        return list(cols)[::-1]

    def process_data(self):
        """
        处理输入数据
        """
        pass

    def process_origin_vibdata(self, data):
        """
        处理振动数据
        把数据库中振动数据，转换为矩阵形式输出
        [[x1,y1,z1],[x2,y2,z2]...[xn,yn,zn]]
        """
        xdata = []
        ydata = []
        zdata = []
        for i in data:
            xdata.extend(i['xdata'])
            ydata.extend(i['ydata'])
            zdata.extend(i['zdata'])
        return xdata, ydata, zdata

    def reduce_vibdata_fre(self, zdata):
        """
        降低振动数据频率
        """

        return zdata[:60]

    @property
    def now(self):
        return datetime.datetime.now()
    def now_str(self):
        return self.now.strftime(settings2.OUTPUT_FILENAME_PATTERN)

    def put_vibdata_to_cloud(self, data):
        companyNo = "CMP20210119001"
        deviceNo = '0001'
        try:

            self.hub.server.invoke("broadcastDJJK_Working", companyNo, deviceNo, self.now.strftime(settings2.OUTPUT_FILENAME_PATTERN), data)
            print("发送%s数据到云端"%data)
        except Exception as e:
            print(e)
            self.ready = False


    def compute_tool_hp(self):
        self.last_computed_time = self.now
        db_data = self.get_vibdata_from_database(limit=60)
        data = []
        for item in db_data:
            fline = np.array(item['zdata'])
            tem = sqrt(np.sum(fline ** 2) / len(fline))
            data.append(tem)
        data = np.array(data)
        data = 1 / (1 + log(data.mean(), 10e12))
        return data

    def test_put_hp_to_mysql(self, val):
        self.cursor.execute("insert into test01(snap, hp) values('{0}', {1})".format(self.now_str, val))
        self.mysql_connect.commit()

    def run(self) -> None:
        """
        每1秒获取一次数据 每次10条 间隔100毫秒
        """
        while 1:
            self.setup()

            while self.ready:

                data = self.get_vibdata_from_database()
                ret = self.process_origin_vibdata(data)
                reduced_ret = self.reduce_vibdata_fre(ret[2])
                if (self.now - self.last_computed_time).seconds >= 2:
                    ret = self.compute_tool_hp()
                    self.test_put_hp_to_mysql(ret)
                    print("健康度%s"%ret)
                self.put_vibdata_to_cloud("振动")
                self.put_vibdata_to_cloud("刀具健康")

                print("当前加工机台->%s, 当前加工刀具->%s, 降频振动:%s"%(self.machine_num, self.tool_num[0], reduced_ret))
                time.sleep(1)

class ProcessMachineInfo(threading.Thread):
    def __init__(self, machine_num, tool_num):
        super().__init__()
        self.machine_num = machine_num
        self.load_list = []
        self.tool_num = tool_num
        self.ready = False


    def setup(self):
        print("正在准备中。。。")
        self.get_mysql_connect()
        self.get_signalr_hub()
        self.ready = True



    def get_signalr_hub(self):
        try:
            self.session = Session()
            self.connection = Connection("http://202.104.118.59:8070/signalr/", self.session)
            self.hub = self.connection.register_hub('dashBoardHub')
            self.connection.start()
        except Exception as e:
            print(e)
            self.ready = False

    @property
    def now(self):
        return datetime.datetime.now()

    def get_mysql_connect(self):
        try:
            self.mysql_connect = pymysql.connect(**settings2.mysql_info)
            self.cursor = self.mysql_connect.cursor()
        except Exception as e:
            print(e)
            self.ready = False

    def get_machineinfodata_from_database(self):
        """
        获取和处理机台信息
        """
        self.cursor.execute("select * from machine_info where machine_num={0};".format(self.machine_num))
        ret = self.cursor.fetchone()
        self.mysql_connect.commit()
        tool_num = ret['tool_position']
        c_pre_cut = float(ret['c_pre_cut'])
        c_act_cut = float(ret['c_act_cut'])
        load = c_pre_cut/c_act_cut
        return tool_num, load

    def set_tool_num(self, num):
        self.tool_num[0] = num



    def compute_load(self, load):
        self.load_list.extend([load] * 5)
        if len(self.load_list) >= 50:
            self.put_to_cloud("broadcastDJJK_FZ", self.load_list)
            self.load_list = []


    def put_to_cloud(self, type, data):
        companyNo = "CMP20210119001"
        deviceNo = '0001'
        try:
            self.hub.server.invoke(type, companyNo, deviceNo,
                                   self.now.strftime(settings2.OUTPUT_FILENAME_PATTERN), "data")
            print("发送%s数据到云端" % data)
        except Exception as e:
            print(e)
            self.ready = False

    def run(self) -> None:
        """
        每50ms获取一次机台信息 每总计1分钟发送一次数据到云端

        """
        while 1:
            self.setup()
            while self.ready:
                tool_num, load = self.get_machineinfodata_from_database()
                self.set_tool_num(tool_num)
                self.compute_load(load)
                #print("当前加工机台->%s, 当前加工刀具->%s, load:%s"%(self.machine_num, tool_num, load))
                time.sleep(0.1)

if __name__ == '__main__':



    t = []
    tool_num1 = [0]
    t.append(ProcessVibData("machine01", tool_num1))
    t.append(ProcessMachineInfo("1", tool_num1))
    for t1 in t:
        t1.start()
    for t1 in t:
        t1.join()