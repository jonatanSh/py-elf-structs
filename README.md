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
    struct command;
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