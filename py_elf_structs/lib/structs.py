import cstruct
from collections import OrderedDict
import logging
from py_elf_structs.lib.utils import log_traceback


class TypeInformationNotFound(Exception):
    pass


class StructBuildException(Exception):
    pass


class LazyResolveStruct(object):
    """
    This class is used in the recursive resolver, read its documentation
    """

    def __init__(self, struct_definition, struct_name, endian, has_padding):
        self.struct_definition = struct_definition
        self.struct_name = struct_name
        self.endian = endian
        self.has_padding = has_padding
        self.__struct_name__ = struct_name

    def resolve(self, structs):
        # Reference for struct inside a struct
        # https://github.com/andreax79/python-cstruct/blob/master/examples/who.py
        for struct in structs:
            if struct.__struct_name__ in self.struct_definition.values():
                for key in self.struct_definition:
                    if self.struct_definition[key] == struct.__struct_name__:
                        del self.struct_definition[key]
                        self.struct_definition[key] = "struct {}".format(struct.__struct_name__)
        try:
            return build_struct(self.struct_name,
                                "\n".join(
                                    ["{} {};".format(str(self.struct_definition[key]), str(key)) for key in
                                     self.struct_definition]),
                                self.endian, self.has_padding)
        except Exception as e:
            log_traceback()
            logging.info("Resolve exception: {}".format(e))
            logging.info("Struct definition: {}".format(self.struct_definition))


def recursively_resolve_remaining_structs(structs, lazy_resolvers):
    """
    The idea beyond this function is that there are many recursive declaration of structs eg ..
    struct a{
        int a;
    }
    struct b {
        struct a;
    }

    struct c{
        struct b;
    }

    C can only be declared after b has been declared and the same is true for b.
    therefore we recursively try to resolve this structs until no change detect
    """
    post_resolve_len = len(structs) + 1
    pre_resolve_len = len(structs)
    while pre_resolve_len != post_resolve_len:
        pre_resolve_len = len(structs)
        resolvers_to_remove = []
        for struct in lazy_resolvers:
            resolved_struct = struct.resolve(structs)
            if resolved_struct:
                lazy_resolvers.remove(struct)
                for i in range(len(structs)):
                    if structs[i].__struct_name__ == struct.struct_name:
                        structs[i] = resolved_struct

        for resolver in resolvers_to_remove:
            resolver.remove(resolver)
        post_resolve_len = len(structs)

    # Now removing all lazy resolve objects
    keys_to_delete = []
    for struct in structs:
        if isinstance(struct, LazyResolveStruct):
            keys_to_delete.append(struct)

    for key in keys_to_delete:
        structs.remove(key)

    return structs


def build_struct(struct_name, c_struct, endian, has_padding):
    class Struct(cstruct.CStruct):
        __struct__ = str(c_struct)
        __endian__ = endian
        __has_padding__ = has_padding
        __struct_name__ = struct_name
        __name__ = __struct_name__

        if endian == "little":
            __byte_order__ = cstruct.LITTLE_ENDIAN
        else:
            __byte_order__ = cstruct.BIG_ENDIAN

        def __init__(self, *args, **kwargs):
            if has_padding['little']:
                kwargs.update({"__padding__": ""})
            if has_padding["big"]:
                kwargs.update({"__big__endian__padding__": ""})
            super(Struct, self).__init__(*args, **kwargs)

        if endian == "little":
            __byte__order = cstruct.LITTLE_ENDIAN
        elif endian == "big":
            __byte__order = cstruct.BIG_ENDIAN
        else:
            raise Exception("Unknown endian: {}".format(endian))

    logging.info("Caching struct: {}".format(struct_name))
    cstruct.STRUCTS[struct_name] = Struct

    return Struct


def type_information_resolve_recursively(dwarf, child, parent):
    """
    Recursively resolving until getting into the base type
    """
    offset = child.attributes['DW_AT_type'].value
    cu = child.cu
    type_information = dwarf.get_DIE_from_refaddr(offset + cu.cu_offset)
    if type_information.is_null():
        raise TypeInformationNotFound("struct: {} attribute: {} maybe typedef ?".format(
            parent.get_full_path(),
            child.get_full_path()
        ))

    if 'DW_AT_type' in type_information.attributes:
        if type_information.attributes['DW_AT_type'].form == "DW_FORM_ref4":
            return type_information_resolve_recursively(dwarf=dwarf, child=type_information,
                                                        parent=parent)

    return type_information


def complex_gcc_types_resolve(type_name):
    if type_name == "short unsigned int":
        return "short"
    if type(type_name) is bytes:
        type_name = type_name.decode("utf-8")
    return type_name


def build_struct_from_pyelf_child(dwarf, pyelf_child, endian):
    """
    Building a new struct from dwarf information.
    this function may return LazyResolveStruct for further resolution in the recursive resolver
    refer to the recursive resolver documentation for further information.
    """
    child_definition = OrderedDict()
    total_size = pyelf_child.attributes['DW_AT_byte_size'].value
    total_calculated_size = 0
    has_padding = {"little": False, "big": False}
    last_sizes = []
    children = [child for child in pyelf_child.iter_children()]
    struct_extra_padding = 0
    logging.info("Struct: {} has {} members".format(
        pyelf_child.get_full_path(),
        len(children)
    ))
    for i, child in enumerate(children):
        next_child_offset = None
        current_offset = child.attributes['DW_AT_data_member_location'].value
        if type(current_offset) is not int:
            current_offset = current_offset[1]
        next_offset = None
        if i + 1 < len(children):
            next_child = children[i + 1]
            next_child_offset_in_struct = next_child.attributes['DW_AT_data_member_location'].value
            if type(next_child_offset_in_struct) is not int:
                next_child_offset = next_child_offset_in_struct[1]
            else:
                next_child_offset = next_child_offset_in_struct
        else:
            next_offset = total_size - current_offset
        type_information = type_information_resolve_recursively(
            dwarf=dwarf,
            child=child,
            parent=pyelf_child
        )
        if next_child_offset:
            next_offset = next_child_offset - current_offset
        if 'DW_AT_name' not in type_information.attributes:
            """
            Should recursively iterate children
            """
            raise Exception("Probably a function typedef not supported for now")

        type_name = type_information.attributes['DW_AT_name'].value
        if not type_name:
            raise TypeInformationNotFound("Type name error got None struct: {} child: {}".format(
                pyelf_child.get_full_path(),
                child.get_full_path()
            ))
        # TODO support arrays, should support offsets for children
        type_size = type_information.attributes['DW_AT_byte_size'].value
        attribute_name = child.get_full_path()
        last_sizes.append(type_size)
        if attribute_name in ["size"]:
            attribute_name = "_size"  # Must override, it is used by cstruct
        # Why the fuck next offset can be lower then type size
        # TODO fix this ?
        if not next_offset or next_offset < type_size:
            total_calculated_size += type_size
        elif next_offset >= type_size:
            total_calculated_size += next_offset
            struct_extra_padding = next_offset % type_size
            array_size = int(next_offset / type_size)
            if array_size > 1:
                attribute_name = attribute_name + "[{}]".format(array_size)
        child_definition[attribute_name] = complex_gcc_types_resolve(type_name)

    if struct_extra_padding != 0:
        has_padding["little"] = True
        child_definition["__padding__[{}]".format(struct_extra_padding)] = "char"
    try:
        return build_struct(pyelf_child.get_full_path(),
                            "\n".join(
                                ["{} {};".format(str(child_definition[key]), str(key)) for key in child_definition]),
                            endian, has_padding)
    except Exception as e:
        logging.info("Simple resolve error: {}".format(e))
        # Maybe this struct is recursive and we should lazy resolve it ?
        return LazyResolveStruct(child_definition, pyelf_child.get_full_path(),
                                 endian, has_padding)
