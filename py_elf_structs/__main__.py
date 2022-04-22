import sys
from py_elf_structs.lib.parser import parse_elf_and_get_structs
import json
import logging


def print_usage_and_exit():
    print("Usage __main__.py <src_file> <output_file> <verbose(optional)>")
    sys.exit(1)


if len(sys.argv) < 3:
    print_usage_and_exit()

if "--help" in sys.argv:
    print_usage_and_exit()

src_file = sys.argv[1]
output_file = sys.argv[2]
verbose = False
verbose_arg = '' if len(sys.argv) < 4 else sys.argv[3]

if verbose_arg.lower() in ["verbose", 'true', '-v']:
    logging.basicConfig(level=logging.INFO)
elif verbose_arg:
    print("Unknown option for verbose use -v")
    print_usage_and_exit()

structs = parse_elf_and_get_structs(src_file)
with open(output_file, "wb") as fp:
    fp.write(json.dumps(structs.__getstate__(), indent=2))

print("Type information for {} generated {}".format(
    src_file,
    output_file
))
