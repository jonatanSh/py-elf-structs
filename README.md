# Py-elf-structs
This repository parse dwarf information from elfs and generate python structs accordingly



# Usage
First lets write our elf:

```c
struct command {
    char command[128];
};

struct command_with_args {
    char arg1[128];
    struct command;
}

```

While compiling we must generate type information:

```bash
gcc main.c -dwarf-2 -ggdb -o a.out
```

Then generate python structs

```python
python -m py_elf_structs a.out /tmp/structs.pickle
```

Finally, load the structs and interact with them

```python
from py_elf_structs import load_structs

structs = load_structs("/structs.pickle")

command_with_args = structs.command_with_args(arg="/tmp", 
                          command=structs.command(
                              command="ls -la"
                          ))

# You can pack this struct
command_with_args.pack()

# Unpack is also supported
command_with_args = structs.command_with_args.unpack("<stream>")
```