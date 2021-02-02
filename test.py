import threading

sign = 1

class Thread1(threading.Thread):
    def __init__(self):
        super().__init__()

    def setattribute(self):
        global sign
        sign = 2
    def run(self) -> None:
        self.setattribute()
class Thread2(threading.Thread):
    def __init__(self):
        super().__init__()


    def getattribute(self):
        global sign
        print(sign)

    def run(self) -> None:
        self.getattribute()

if __name__ == '__main__':
    t1 = Thread1()

    t2 = Thread2()
    t1.start()
    t2.start()
    t1.join()
    t2.join()