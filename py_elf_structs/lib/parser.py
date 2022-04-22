from py_elf_structs.lib.structs import build_struct_from_pyelf_child, \
    TypeInformationNotFound, StructBuildException, LazyResolveStruct, recursively_resolve_remaining_structs, \
    build_struct
from elftools.elf.elffile import ELFFile
import logging


class StructHolder(object):
    def __init__(self, structs):
        self.___structs = structs
        self._struct_map = {}

    def __getattr__(self, item):
        if item in ["___structs", "__repr__", "__str__", "display", '_struct_map', 'struct_map']:
            return super(StructHolder, self).__getattribute__(item)

        return self.struct_map[item]

    @property
    def struct_map(self):
        if not self._struct_map:
            for struct in self.___structs:
                self._struct_map[struct.__struct_name__] = struct
        return self._struct_map

    def __repr__(self):
        return repr(self.struct_map)

    def __str__(self):
        return repr(self)

    def __getstate__(self):
        pickled_object = []
        for struct in self.___structs:
            pickled_object.append({
                "c_struct": struct.__struct__,
                "endian": struct.__endian__,
                "has_padding": struct.__has_padding__,
                "struct_name": struct.__struct_name__
            })
        return pickled_object

    def __setstate__(self, state):
        self.___structs = []
        for obj in state:
            self.___structs.append(build_struct(**obj))

    def display(self):
        for struct in self.___structs:
            print("-" * 30)
            print(struct.__struct_name__)
            print(struct.__struct__)
            print("-" * 30)


def parse_elf_and_get_structs(elf_path):
    structs = []
    lazy_resolve = []
    logging.info("Parsing: {}".format(elf_path))
    with open(elf_path, 'rb') as fp:
        elf = ELFFile(fp)
        if not elf.has_dwarf_info():
            raise Exception("Dwarf information not found on elf")
        dwarf = elf.get_dwarf_info()
        endian = 'big'
        if dwarf.config.little_endian:
            endian = "little"
        logging.info("Elf endian: {}".format(endian))
        cus = [c for c in dwarf.iter_CUs()]
        dies = [c.get_top_DIE() for c in cus]

        for die in dies:
            for child in die.iter_children():
                if child.tag == "DW_TAG_structure_type":
                    logging.info("Parsing struct: {}".format(child.get_full_path()))
                    try:
                        struct_obj = build_struct_from_pyelf_child(dwarf,
                                                                   child,
                                                                   endian)
                        if isinstance(struct_obj, LazyResolveStruct):
                            lazy_resolve.append(struct_obj)
                        structs.append(struct_obj)
                    except (TypeInformationNotFound, StructBuildException, Exception) as e:
                        logging.info("Parsing exception: {}".format(e))

    # Actually this function should be recursive !
    # Because one struct can define many structs !
    structs = recursively_resolve_remaining_structs(structs=structs, lazy_resolvers=lazy_resolve)
    structs = set(structs)
    logging.info("Found: {} structs".format(len(structs)))
    return StructHolder(structs)
