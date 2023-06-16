import sys
import code

import dill
from tblib import pickling_support
from rich import print
from rich.traceback import Traceback



def install(file="debug.pkl"):
    pickling_support.install()
    old_excepthook = sys.excepthook
    def new_hook(type, value, traceback):
        save_object = {
            "type": type,
            "value": value,
            "traceback": traceback,
            "globals": {
                dill.dumps(k): dill.dumps(v)
                for k, v in globals().items()
            }
        }
        with open('debug.pkl', 'wb') as file:
            dill.dump(save_object, file)
        print("Traceback saved to debug.pkl")
        old_excepthook(type, value, traceback)
    
    sys.excepthook = new_hook


def drop_in(file="debug.pkl"):
    with open(file, 'rb') as f:
        trace_object = dill.load(f)
    print(
        Traceback.from_exception(
            trace_object["type"],
            trace_object["value"],
            trace_object["traceback"],
            extra_lines=10,

        ),
    )
    for k, v in trace_object["globals"].items():
        globals()[dill.loads(k)] = dill.loads(v)
    code.interact(banner="mondo debugging dude!")
    
