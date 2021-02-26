import pymysql
import settings2


conn = pymysql.connect(**settings2.mysql_info)
print(conn)
cur = conn.cursor()
cur.execute("select * from machine_info where machine_num=1;")
ret = cur.fetchone()
print(ret)


def get_mysql_connect():
    """
    获取上传刀具健康度的mysql连接
    """
    mysql_connect = pymysql.connect(**settings2.hp_mysql_info)
    cursor = mysql_connect.cursor()
    return cursor, mysql_connect

def test_put_hp_to_mysql(snap, val):
    cursor, mysql_connect = get_mysql_connect()
    cursor.execute("insert into test01(snap, hp) values('{0}', {1})".format(snap, val))
    ret = cursor.fetchone()
    mysql_connect.commit()
    print(ret)
test_put_hp_to_mysql("2020", 2)
test_put_hp_to_mysql("2021", 1)