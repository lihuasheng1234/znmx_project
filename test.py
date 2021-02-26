import threading
import time
sign = 1

class Thread1(threading.Thread):
    def __init__(self, a, c):
        super().__init__()
        self.a = a
        self.c = c

    def setattribute(self, b):
        self.a[0] = b
    def run(self) -> None:
        for i in range(10):
            if i > 2:
                self.setattribute(self.c)
                print('----')
            else:
                self.setattribute(2)
            time.sleep(1)
class Thread2(threading.Thread):
    def __init__(self, a):
        super().__init__()
        self.a = a

    def getattribute(self):
        print(self.a[0])
    def run(self) -> None:
        while 1:
            self.getattribute()
            time.sleep(1)
if __name__ == '__main__':
    t = []
    var1 = [0]
    var2 = [3]
    t.append(Thread1(var1,5))
    t.append(Thread2(var1))
    t.append(Thread1(var2,7))
    t.append(Thread2(var2))
    for i in t:
        i.start()
    for i in t:
        i.join()