import sys
from py_elf_structs.lib.parser import parse_elf_and_get_structs
import json
import logging
from py_elf_structs import generate_structs


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
    verbose = True
elif verbose_arg:
    print("Unknown option for verbose use -v")
    print_usage_and_exit()

generate_structs(src_file=src_file,
                 output_file=output_file,
                 is_verbose=verbose)
