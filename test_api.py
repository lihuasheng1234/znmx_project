import requests


times = 5
start_date = '2021-02-24 14:13:00'
test_data = "7, 20, -2, 10, 16, 11, 10, 21, 11, 14, -4, -4, 5, 3, 13, -12, -1, 13, -1, -3, -9, -11, 14, 27, 2, -17, 11, 9, 18, 7, -22, -21, -1, 5, -10, 6, 11, 10, 32, 5, 6, 22, 4, 4, 12, 14, 26, 50, 20, -5, 12, 22, 15, 8, 10, 6, -12, 15, 6, 9"
test_data = test_data.split(",")
test_data = test_data*times

url = "http://202.104.118.59:8054/api/TblDeviceFanuc/InsertToolDetect"
data = {
    "company_no":"CMP20210119001",
    "device_no":"0001",
    "tool_position":"raw",
    "collect_data":",".join(test_data),
    "collect_date": start_date,

}
headers = {
    # "Content-Type": "application/x-www-form-urlencoded"
}
print(data)

resp = requests.post(url, data=data, headers=headers)

print(resp.text)
print(resp.request.headers)
print(resp.headers)