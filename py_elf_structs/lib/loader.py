import json
import os
from py_elf_structs.lib.parser import StructHolder


def load_structs(path_to_pickled_object):
    if not os.path.exists(path_to_pickled_object):
        print("{} does not exists".format(path_to_pickled_object))
    with open(path_to_pickled_object, "rb") as fp:
        data = json.load(fp)

    structs = StructHolder(None)
    structs.__setstate__(data)
    return structs
