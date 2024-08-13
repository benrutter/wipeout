# Wipeout 🌊

*Savable/debuggable exceptions*

Note: this project contains code taken from the awesome, but no longer maintained [pydump](https://github.com/elifiner/pydump)

## Motivation

Ever wish you could just jump into debugging an error that happened in production?

Wipeout will let you do that (with a few limitations at the moment)

It overrides the python system exception hook (the thing that happens when python crashes out due to an unhandled error) so that before exiting, a rerunnable traceback will be saved.

Wipeout also makes use of the great library *fsspec* so that you can save/load debug sessions to a variety of storage options (local, s3, azure blob, ssh, etc etc).

## How to

### Install

```bash
pip install wipeout
```

### Use to store and load exceptions

Here's a simple example to save to a static file:

```python
import wipeout

wipeout.install(lambda: "~/coolfile.wipeout")
```

After that, if the code hits an error, it'll save a debug session to that location, which can later be triggered with:

```bash
python -m wipeout.load --file ~/coolfile.wipeout
```

The above command will open up a postmortem session in your debugger of choice (based on your `PYTHONBREAKPOINT` environment variable) where your error happened.

You might want to include a date or something so that multiple errors don't overwrite each other.

```python
from datetime import datetime

import wipeout

def filename_function():
  date_string = datetime.now().strftime("%Y%m%d%H%S%f")
  return f"~/cool_{date_string}.wipeout"

wipeout.install(filename_function)
```

And you can pass in storage options plus an fsspec prefix if you wanted to save in the cloud (see fsspec for more details):

```python
from datetime import datetime

import wipeout

def filename_function():
  date_string = datetime.now().strftime("%Y%m%d%H%S%f")
  return f"abfs://someplace/cool_{date_string}.wipeout"

wipeout.install(filename_function, storage_options={"account_name": "blobstore", "anon": False})
```


### Run mode

Wipeout also has a "run mode" which is a quick command to support running a python script as normal, but jumping into a debug session if an error is raised:

```bash
python -m wipeout.run rad/python/script.py
```
