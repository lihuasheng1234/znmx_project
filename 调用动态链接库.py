import os
from ctypes import *

os.add_dll_directory('D:\django projects\hy\znmx_project-master\Debug');
dll = cdll.LoadLibrary('api.dll');

ret = dll.setAlarm(2, 0);
print(ret)