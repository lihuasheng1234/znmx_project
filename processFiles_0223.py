from gevent import monkey
monkey.patch_all()

from functools import wraps
import threading
import time
import datetime
from math import sqrt, log
import numpy as np
import pymongo
import pymysql
from signalr import Connection
from requests import Session
from datetime import timedelta

import settings

"""

"""
class ProcessData(threading.Thread):
    def __init__(self):
        super().__init__()
        self.dic = {}
        self.last_transform_time = self.now
        self.vibData_cache = []
        self.raw_vibData_cache = []
        self.load_cache = []
        self.pre_data = None
        self.user_settings = {}
        self.feed = 0
        self.rspeed = 0
        self.tool_num = 0
        self.load = 0
        self.tool_hp = 0

    @property
    def now(self):
        return datetime.datetime.now()

    @property
    def now_str(self):
        return self.now.strftime(settings.DATETIME_PATTERN)

    def clothes(blanking_time, flag=False):
        """
        限制函数的执行间隔
        参数 blanking_time: 间隔时间
            flag: 如果为True 将在指定时间后执行 否则立马执行
        """
        def decorate(func):
            @wraps(func)
            def ware(self, *args, **kwargs):
                last_time = self.dic.get(func)

                if not last_time:
                    ret = None
                    if not flag:
                        ret = func(self, *args, **kwargs)
                    self.dic[func] = self.now
                    return ret
                elif (self.now - last_time) >= timedelta(milliseconds=blanking_time):
                    self.dic[func] = self.now
                    return func(self, *args, **kwargs)
            return ware
        return decorate



    def setup(self):
        print("正在准备中。。。")
        try:
            self.get_mangodb_connect()
            # self.get_mysql_connect()
            # self.get_signalr_hub()
            self.ready = True
        except Exception as e:
            print(e)
            self.ready = False

    def get_mangodb_connect(self):
        """
        获取mongodb连接
        """
        self.mangodb_connect = pymongo.MongoClient(settings.mangodb_info['host'], serverSelectionTimeoutMS=settings.mangodb_info['connect_timeoutMS'])
        dblist = self.mangodb_connect.list_database_names()

    def get_mysql_connect(self):
        """
        获取上传刀具健康度的mysql连接
        """
        self.mysql_connect = pymysql.connect(**settings.hp_mysql_info)
        self.cursor = self.mysql_connect.cursor()

    def get_signalr_hub(self):
        """
        获取websocket连接
        """
        self.session = Session()
        self.connection = Connection(settings.signalr_hub_info['url'], self.session)
        self.hub = self.connection.register_hub(settings.signalr_hub_info["name"])
        self.connection.start()

    @clothes(settings.VIBDATA_DB_GET_BLANKING_TIME)
    def prepare_vibrationData(self):
        """
        每个一秒钟从数据库中获取一次振动数据并处理成相应格式
        """
        origin_data = self.get_origin_vibrationData()
        self.process_vibrationData(origin_data)
        self.make_vibDate_cache()

    def get_origin_vibrationData(self, limit=settings.VIBDATA_COUNT):
        """
        从数据库中获得原始数据
        """
        cols = self.mangodb_connect["VibrationData"]["Sensor01"].find({}, sort=[('_id', pymongo.DESCENDING)],
                                                                      limit=limit)
        return list(cols)[::-1]

    def process_vibrationData(self, db_data):
        """
        把数据库请求得到的数据处理成对应结果
        通过self.pre_data存放
        """
        data = []
        for item in db_data:
            data.extend(item['zdata'])
        self.pre_data = data
        return data


    @clothes(200)
    def prepare_machineInfo(self):
        origin_machineinfo = self.get_origin_machineinfo()
        self.set_machineinfo(origin_machineinfo)
        self.make_load_cache()

    def make_load_cache(self):
        self.load_cache.append(self.load)

    @clothes(3000, flag=True)
    def 发送负载数据到云端(self):
        print("发送负载到云端%s"%self.load_cache)
        self.load_cache = []


    def get_origin_machineinfo(self):
        return {"Feed": 6000, "RSpeed": 8000, "tool_num":"T01", 'load':0.5}

    def set_machineinfo(self, origin_machineinfo):
        self.feed = origin_machineinfo["Feed"]
        self.rspeed = origin_machineinfo["RSpeed"]
        self.tool_num = origin_machineinfo["tool_num"]
        self.load = origin_machineinfo["load"]
        self.set_machineinfo_from_file()

    def set_machineinfo_from_file(self):
        """
        获取并设定用户提供的机台刀具信息
        """
        self.user_settings = {
            "T01":{
                "feed": 6000,
                "rspeed": 8000,
                "model": 1,
                "var1": 8000,
                "var2": 8000,
            },
            "T02": {
                "feed": 8000,
                "rspeed": 8000,
                "model": 2,
                "var1": 8000,
                "var2": 8000,
            }
        }

    def make_vibDate_cache(self):
        """
        把振动数据缓存起来

        """
        if not self.判断刀具是否转向():
            self.vibData_cache.append(self.pre_data)

        self.raw_vibData_cache.extend(self.pre_data)

    def 判断刀具是否转向(self):

        if self.tool_num in self.user_settings and  (self.user_settings[self.tool_num]["feed"] != self.feed or self.user_settings[self.tool_num]["rspeed"] != self.rspeed):
            return True
        pass

    @clothes(settings.RAWVIBDATA_UPLOAD_BLANKING_TIME)
    def 发送振动数据到云端(self):
        self.处理振动数据()
        print("发送振动数据到云端%s"%self.processed_raw_vibData)
        self.raw_vibData_cache = []


    def 处理振动数据(self):
        self.processed_raw_vibData = self.raw_vibData_cache[:60]

    @clothes(settings.TOOLHEALTH_COMPUTE_BLANKING_TIME, True)
    def 处理健康度(self):
        self.运行对应算法计算健康度()
        self.发送健康度到云端()
        self.健康度报警()
        self.clean_vibdata_cache()
        pass

    def 健康度报警(self):
        print("健康度报警")

    def 运行对应算法计算健康度(self):
        model = self.user_settings[self.tool_num]["model"]

        ret = self.计算健康度(self.vibData_cache)

        self.tool_hp = ret

    def 计算健康度(self, data):
        return 1

    def 发送健康度到云端(self):

        print("发送到云端:健康度->%s,刀具->%s"%(self.tool_hp, self.tool_num))

    def clean_vibdata_cache(self):
        self.vibData_cache = []

    @clothes(1000)
    def show_info(self):
        """
        显示当前算法运行状况
        """
        print("当前时间:{0},上次计算健康度时间时间:{1},当前机台->加工刀具:{2},转速:{3},进给:{4},负载:{5},当前健康度:{6},当前振动数据:{7},当前振动缓存数据{8},当前健康度缓存数据{9}".format(self.now_str, self.last_transform_time, self.tool_num,
                                                                                                         self.rspeed, self.feed, self.load, self.tool_hp, len(self.pre_data), len(self.raw_vibData_cache), self.vibData_cache[0]))



    def run(self) -> None:
        """
        每1秒获取一次数据 每次10条 间隔100毫秒
        """
        while 1:
            self.setup()
            while self.ready:
                self.prepare_vibrationData()
                self.prepare_machineInfo()
                self.处理健康度()
                self.发送振动数据到云端()
                self.发送负载数据到云端()
                self.show_info()
                time.sleep(0.1)
            if not self.ready:
                print("五秒后重试")
                time.sleep(5)

if __name__ == '__main__':



    t = []
    tool_num1 = [0]
    t.append(ProcessData())
    for t1 in t:
        t1.start()
    for t1 in t:
        t1.join()