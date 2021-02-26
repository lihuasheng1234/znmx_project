import pymysql

import settings2

conn = pymysql.connect(**settings2.mysql_info)
print(conn)
cur = conn.cursor()
print(cur.execute("UPDATE machine_info SET tool_position = 2,c_cut='1:0.5' where id = 0;"))
print(cur.fetchone())
cur.execute("select * from machine_info order by id limit 1;")

print(cur.fetchone())
conn.commit();