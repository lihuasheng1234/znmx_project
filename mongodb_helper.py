import pymongo

myclient = pymongo.MongoClient('mongodb://192.168.1.81:27017/', serverSelectionTimeoutMS=2000)

dblist = myclient.list_database_names()
print(dblist)
mydb = myclient["VibrationData"]["Sensor01"].find({}, sort=[('_id', pymongo.DESCENDING)], limit=100)


# for doc in mycol.find({},{ "_id": 1}, sort=[('_id', pymongo.DESCENDING)], limit=1000):
#  doc in mycol.find({},{ "_id": 1}, sort=[('_id', pymongo.DESCENDING)], limit=1000)   print(doc)
doc = list(mydb)[::-1]
xdata = []
ydata = []
zdata = []
for i in doc:
    # print(i)
    # print(i['xdata'])
    xdata.extend(i['xdata'])
    ydata.extend(i['ydata'])
    zdata.extend(i['zdata'])
# print(len(xdata))
myclient.close()