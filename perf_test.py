##############
# perf test with multiprocessing
from multiprocessing import Pool, Process
import os
import time
import urllib.request


def info(title):
    print(title)
    print('module name:', __name__)
    print('parent process:', os.getppid())
    print('process id:', os.getpid())

def f(x):
	info('function f')
	url = 'http://localhost:8080/take/?route=GET%20fastCall'
	print(f"call {x}")
	return urllib.request.urlopen(url).status




if __name__ == '__main__':
    p = Process(target=f, args=('bob',))
    p.start()
    p.join()

    with Pool(10) as p:
        print(p.map(f, range(1, 10000)))

