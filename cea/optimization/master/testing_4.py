from __future__ import print_function
from scoop import futures

def helloWorld(value):
    return "Hello World from Future #{0}".format(value)

if __name__ == "__main__":
    returnValues = list(futures.map(helloWorld, range(16)))
    print("\n".join(returnValues))