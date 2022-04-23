# Py-elf-structs
This repository parse dwarf information from elfs and generate python structs accordingly



# Usage
First lets write our elf:

```c
struct command {
    char command[64];
};

struct command_with_args {
    char arg1[128];
    struct command command;
};
/*
    Ignore this part it is only done for disabling optimization
    Optimization will omit the structs if they are not being used 
    -O0 omits this structs from the output for some reason
*/
void main() {
    struct command a = {};
    struct command_with_args b = {};
    printf("a = %p, b=%p\n", a, b);
}

```

While compiling we must generate type information:

```bash
gcc main.c -dwarf-2 -ggdb -o a.out
```

Then generate python structs

```python
python -m py_elf_structs a.out /tmp/structs.json
```

Finally, load the structs and interact with them

```python
from py_elf_structs import load_structs

structs = load_structs("/tmp/structs.json")

command_with_args = structs.command_with_args(arg="/tmp", 
                          command=structs.command(
                              command="ls -la"
                          ))

# You can pack this struct
command_with_args.pack()

# Unpack is also supported
command_with_args = structs.command_with_args.unpack("<stream>")
```

You can also use a python api to generate the structs.json file:
```python
from py_elf_structs import generate_structs
src_file="a.out"
output_file="/tmp/structs.json"
verbose=True
generate_structs(src_file=src_file,
                 output_file=output_file,
                 is_verbose=verbose)
```

# Protected attributes
Attribute with the name size is used by the parser therefor if a struct contain a variable named
size it is replaced by _size
eg ..
```c
struct my_struct {
    int size;
}
```
python api:
```python
from py_elf_structs import load_structs
structs = load_structs("/tmp/structs.json")
structs.my_struct(_size=2)
```

# Struct alignment
Struct maybe aligned to sizeof(ptr) therefore we should support this
eg ...
```c
struct command {
    unsigned int address;
    unsigned short value;
};
```
The resulting cstruct is:
```c
struct command {
    unsigned int address;
    unsigned short value[2];
};
```
Because this struct is aligned to 4 it is handled by the api and you can create this struct anyway:
```python
from py_elf_structs import load_structs

structs = load_structs("/tmp/structs.json")

structs.command(address=1, value=2)
# This will create the struct and fix value to be an array
```

