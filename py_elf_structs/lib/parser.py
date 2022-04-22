from structs import build_struct_from_pyelf_child, \
    TypeInformationNotFound, StructBuildException, LazyResolveStruct, recursively_resolve_remaining_structs, \
    build_struct
from elftools.elf.elffile import ELFFile


class StructHolder(object):
    def __init__(self, structs):
        self.___structs = structs

    def __getattr__(self, item):
        if item in ["___structs", "__repr__", "__str__", "display"]:
            return super(StructHolder, self).__getattribute__(item)
        return self.___structs[item]

    def __repr__(self):
        return repr(self.___structs)

    def __str__(self):
        return repr(self)

    def __getstate__(self):
        pickled_object = []
        for struct_name, struct in self.___structs.items():
            pickled_object.append({
                "c_struct": struct.__struct__,
                "endian": struct.__endian__,
                "has_padding": struct.__has_padding__,
                "struct_name": struct.__struct_name__
            })
        return pickled_object

    def __setstate__(self, state):
        self.___structs = {}
        for obj in state:
            self.___structs[obj['struct_name']] = build_struct(**obj)

    def display(self):
        for key in self.___structs:
            print "-" * 30
            print key
            print self.___structs[key].__struct__
            print "-" * 30


def parse_elf_and_get_structs(elf_path):
    structs = {}
    lazy_resolve = []
    with open(elf_path) as fp:
        elf = ELFFile(fp)
        if not elf.has_dwarf_info():
            raise Exception("Dwarf information not found on elf")
        dwarf = elf.get_dwarf_info()
        endian = 'big'
        if dwarf.config.little_endian:
            endian = "little"
        cus = [c for c in dwarf.iter_CUs()]
        dies = [c.get_top_DIE() for c in cus]

        for die in dies:
            for child in die.iter_children():
                if child.tag == "DW_TAG_structure_type":
                    try:
                        struct_obj = build_struct_from_pyelf_child(dwarf,
                                                                   child,
                                                                   endian)
                        if isinstance(struct_obj, LazyResolveStruct):
                            lazy_resolve.append(struct_obj)
                        structs[child.get_full_path()] = struct_obj
                    except (TypeInformationNotFound, StructBuildException, Exception) as e:
                        pass

    # Actually this function should be recursive !
    # Because one struct can define many structs !
    structs = recursively_resolve_remaining_structs(structs=structs, lazy_resolvers=lazy_resolve)
    return StructHolder(structs)
