import pymysql

# 时间字符串格式
DATETIME_PATTERN = "%Y-%m-%d-%H-%M-%S"

# 负载小于到少判断为主轴未转动
MIN_VALUE = 0

#mysql settings
mysql_info = {
    "host" : "192.168.1.33",  # mysql服务端ip
    "port" : 3306,  # mysql端口
    "user" : "root",  # mysql 账号
    "password" : "root",
    "db" : "znmx",
    "charset" : "utf8",
    "cursorclass" : pymysql.cursors.DictCursor
}


# 计算健康度时间间隔 毫秒
TOOLHEALTH_COMPUTE_BLANKING_TIME = 5*1000

# 负载上传时间 毫秒
LOADDATA_UPLOAD_BLANKING_TIME = 1*1000

# 原始振动数据上传时间 毫秒
RAWVIBDATA_UPLOAD_BLANKING_TIME = 2*1000

# 数据库中振动数据每条数据间隔 毫秒
VIBDATA_DB_TIME = 100

# 从数据库获取振动数据间隔 毫秒
VIBDATA_DB_GET_BLANKING_TIME = 100

# 每个间隔内从数据库中获取的数据条数
VIBDATA_COUNT = VIBDATA_DB_GET_BLANKING_TIME//VIBDATA_DB_TIME


# 刀具健康度mysql
hp_mysql_info = {
    "host" : "192.168.1.33",  # mysql服务端ip
    "port" : 3306,  # mysql端口
    "user" : "root",  # mysql 账号
    "password" : "root",
    "db" : "znmx",
    "charset" : "utf8",
    "cursorclass" : pymysql.cursors.DictCursor
}

#mangodb settings
mangodb_info = {
    "host" : "mongodb://192.168.1.81:27017/",
    "db_name" : "VibrationData",
    "tb_name" : "Sensor01",
    "connect_timeoutMS" : "10000",
}

signalr_hub_info = {
    "url": "http://202.104.118.59:8070/signalr/",
    "name": "dashBoardHub",
}
