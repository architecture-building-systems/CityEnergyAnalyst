import multiprocessing
import time
import itertools
from functools import partial

def print_func_convert(a_b):
    print (a_b)
    return print_func(*a_b)

def print_func(continent, second_var, constant_k, constant_k2, constant_k3):
    print ('The name of the continent is : ', continent)
    z = loop_func(continent, constant_k)

    print ('The sum is: ', z + second_var + constant_k2 + constant_k3)

def loop_func(continent, constant_k):
    for i in range(10000000):
        i = continent + i
    i = i * constant_k
    return i

if __name__ == "__main__":
    pool = multiprocessing.Pool(10)

    t0 = time.clock()
    constant_k = 5

    # func = partial(print_func, constant_k)
    # pool.map(func, range(20), range(20))
    pool.map(print_func_convert, itertools.izip(range(20), range(20), itertools.repeat(constant_k, 20), itertools.repeat(constant_k, 20), itertools.repeat(constant_k, 20)))

    pool.close()
    pool.join()

    t1 = time.clock()

    for i in range(20):
        print_func(i, i, constant_k, constant_k, constant_k)

    t2 = time.clock()

    print (t1-t0)
    print (t2-t1)