from py_elf_structs.lib.parser import parse_elf_and_get_structs
import json
import logging


def generate_structs(src_file, output_file, is_verbose=False):
    if is_verbose:
        logging.basicConfig(level=logging.INFO)
    structs = parse_elf_and_get_structs(src_file)
    with open(output_file, "w") as fp:
        fp.write(json.dumps(structs.__getstate__(), indent=2))
    print("Type information for {} generated {}".format(
        src_file,
        output_file
    ))
