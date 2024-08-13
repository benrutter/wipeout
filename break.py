import sys

import wipeout

wipeout.install(name_func=lambda: "cool.pkl")


def breakdown():
    nice = 0
    cool = 4
    wikid = cool / nice
    return wikid


def breakstuff():
    return breakdown()


nice = breakstuff()

print(nice)
