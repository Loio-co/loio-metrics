import inspect
import os


def full_name_for(short_name: str) -> str:
    caller_frm = inspect.stack()[1]
    dirname = os.path.dirname(os.path.realpath(caller_frm.filename))
    fullname = os.path.join(dirname, 'texts', short_name)
    return fullname
