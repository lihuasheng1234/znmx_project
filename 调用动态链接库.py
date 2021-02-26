from ctypes import *

dll = cdll.LoadLibrary('hello.dll');
ret = dll.IntAdd(2, 4);
print(ret)