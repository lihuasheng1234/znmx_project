from signalr import Connection
from requests import Session

with Session() as session:
    #create a connection
    connection = Connection("http://202.104.118.59:8070/signalr/", session)

    #get chat hub
    hub = connection.register_hub('dashBoardHub')
    #start a connection
    connection.start()
    #create error handler
    def print_error(error):
        print('error: ', error)
        # process errors
    connection.error += print_error
    companyNo = "CMP20210119001"
    deviceNo = '0001'
    data = "43, 25, 95, 10, 35, 46, 1, 50, 25, 93, 106, 53, 10, 32, 13, 10, 25, 61, 69, 68, 9, 69, 59, 36, 26, 4, 73, 45, 77, 11, 104, 63, 14, 11, 42, 50, 7, 105, 55, 45, 64, 67, 26, 80, 4, 83, 17, 44, 99, 109"
    data_raw = "7, 20, -2, 10, 16, 11, 10, 21, 11, 14, -4, -4, 5, 3, 13, -12, -1, 13, -1, -3, -9, -11, 14, 27, 2, -17, 11, 9, 18, 7, -22, -21, -1, 5, -10, 6, 11, 10, 32, 5, 6, 22, 4, 4, 12, 14, 26, 50, 20, -5, 12, 22, 15, 8, 10, 6, -12, 15, 6, 9"
    data1 = {'data': [43, 25, 95, 10, 35, 46, 1, 50, 25, 93, 106, 53, 10, 32, 13, 10, 25, 61, 69, 68, 9, 69, 59, 36, 26, 4, 73, 45, 77, 11, 104, 63, 14, 11, 42, 50, 7, 105, 55, 45, 64, 67, 26, 80, 4, 83, 17, 44, 99, 109]}
    data2 = {'data': [43, 25, 95, 10, 35, 46, 1, 50, 25, 93, 106, 53, 10, 32, 13, 10, 25, 61, 69, 68, 9, 69, 59, 36, 26, 4, 73, 45, 77, 11, 104, 63, 14, 11, 42, 50, 7, 105, 55, 45, 64, 67, 26, 80, 4, 83, 17, 44, 99, 109]}
    import time, json
    i = 0
    #hub.server.invoke("broadcastDJJK_Health", companyNo, deviceNo, "T01", "2021-01-26 08:38:00", "1")
    while True:

        if i < 10:
            time1 = "2021-01-26 08:38:0" + str(i)
        else:
            time1 = "2021-01-26 08:38:" + str(i)
        #hub.server.invoke("broadcastDJJK_Working", companyNo, deviceNo, time1, data_raw)
        hub.server.invoke("broadcastDJJK_FZ", companyNo, deviceNo, time1, data)
        #if i == 59:
        #hub.server.invoke("broadcastDJJK_Health", companyNo, deviceNo, "T01", time1, "1")
        i += 1
        i = i % 60
        time.sleep(1)
        print(i)