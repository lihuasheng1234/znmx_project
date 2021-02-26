import time, datetime
from functools import wraps

class Foo:
    def __init__(self):
        self.start_time = datetime.datetime.now()
        self.start_time2 = datetime.datetime.now()
        self.dic = {}
    @property
    def now(self):
        return datetime.datetime.now()

    def clothes(snap_time):
        def decorate(func):
            @wraps(func)
            def ware(self, *args, **kwargs):
                last_time = self.dic.get(func)
                if not last_time:
                    ret = func(self, *args, **kwargs)
                    self.dic[func] = self.now
                    return ret
                elif (self.now - last_time).seconds >= snap_time:
                    self.dic[func] = self.now
                    return func(self, *args, **kwargs)
            return ware
        return decorate

    @clothes(1)
    def fun1(self):
        print("foo1 is running")

    @clothes(2)
    def fun2(self):
        print("foo2 is running")
    def run(self):
        while True:
            self.fun1()
            self.fun2()
            time.sleep(0.5)


if __name__ == '__main__':
    f = Foo()
    f.run()