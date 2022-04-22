import sys
from type_information.parser import parse_elf_and_get_structs
import pickle

if len(sys.argv) < 3:
    print("Usage generate_type_information.py <src_file> <output_file>")
    sys.exit(1)

src_file = sys.argv[1]
output_file = sys.argv[2]

structs = parse_elf_and_get_structs(src_file)

with open(output_file, "wb") as fp:
    fp.write(pickle.dumps(structs))

print("Type information for {} generated {}".format(
    src_file,
    output_file
))
