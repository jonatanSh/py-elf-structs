import cstruct
from collections import OrderedDict


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

    def resolve(self, structs):
        # Reference for struct inside a struct
        # https://github.com/andreax79/python-cstruct/blob/master/examples/who.py
        for struct_name, struct in structs.items():
            if struct_name in self.struct_definition.values():
                for key in self.struct_definition:
                    if self.struct_definition[key] == struct_name:
                        del self.struct_definition[key]
                        self.struct_definition["struct {}".format(struct_name)] = key
        try:
            return build_struct(self.struct_name,
                                "\n".join(
                                    ["{} {};".format(self.struct_definition[key], key) for key in
                                     self.struct_definition]),
                                self.endian, self.has_padding)
        except Exception as e:
            pass


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
                structs[struct.struct_name] = resolved_struct

        for resolver in resolvers_to_remove:
            resolver.remove(resolver)
        post_resolve_len = len(structs)

    # Now removing all lazy resolve objects
    keys_to_delete = []
    for key in structs:
        value = structs[key]
        if isinstance(value, LazyResolveStruct):
            keys_to_delete.append(key)

    for key in keys_to_delete:
        del structs[key]

    return structs


def build_struct(struct_name, c_struct, endian, has_padding):
    class Struct(cstruct.CStruct):
        __struct__ = c_struct
        __endian__ = endian
        __has_padding__ = has_padding
        __struct_name__ = struct_name

        if endian == "little":
            __byte_order__ = cstruct.LITTLE_ENDIAN
        else:
            __byte_order__ = cstruct.BIG_ENDIAN

        def __init__(self, **kwargs):
            if has_padding['little']:
                kwargs.update({"__padding__": ""})
            if has_padding["big"]:
                kwargs.update({"__big__endian__padding__": ""})
            super(Struct, self).__init__(**kwargs)

        if endian == "little":
            __byte__order = cstruct.LITTLE_ENDIAN
        elif endian == "big":
            __byte__order = cstruct.BIG_ENDIAN
        else:
            raise Exception("Unknown endian: {}".format(endian))

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
            array_size = next_offset / type_size
            if array_size > 1:
                attribute_name = attribute_name + "[{}]".format(array_size)
        child_definition[attribute_name] = complex_gcc_types_resolve(type_name)

    if total_calculated_size < total_size:
        has_padding["little"] = True
        child_definition["__padding__[{}]".format(total_size - total_calculated_size)] = "char"
    try:
        return build_struct(pyelf_child.get_full_path(),
                            "\n".join(["{} {};".format(child_definition[key], key) for key in child_definition]),
                            endian, has_padding)
    except Exception as e:
        # Maybe this struct is recursive and we should lazy resolve it ?
        return LazyResolveStruct(child_definition, pyelf_child.get_full_path(),
                                 endian, has_padding)
