#!/bin/python3

import os
import random

# output file
C_FILE = "dungeon.c"

# these lines will be included in the target function
CRASH = "\tchar* buff = malloc(8);\n\tputchar(buff[0xffffffff]);\n"

# function pointer mode uses a fp to call the final target func
FP_MODE = True

# internal stuff
name = 0            # name counter for decoy-functions
t_name = 0          # name counter for functions on target path
magic_str = ""      # crashing input


def new_name():
    """ helper func to iterate func names"""
    global name
    name += 1
    return name


def make_func(my_name, depth, spread, max_depth, stump, loop, t_path=False, t_depth=None):
    global name, t_name, magic_str

    is_main = True if (depth == 0) else False
    t_path = True if (is_main) else t_path


    if not t_path:
        # decide if node is leaf
        stump_roll = random.random()
        is_final = True if (stump_roll <= stump or depth == max_depth) else False
    else:
        # decide if this is the final target func
        is_final = True if depth == t_depth else False

    # decide amount of (decoy) children
    if is_main:
        children = spread[1]
    else:
        children = 0
        if not is_final:
            children = random.randint(spread[0], spread[1])

    magic_chr = []  # char in input that triggers the path

    if t_path:
        # generate next func for target path
        if not is_final:
            m_chr = chr(random.randint(32, 126))
            while (m_chr == '\\' or m_chr == '\''):
                    m_chr = chr(random.randint(32, 126))
            magic_chr.append(m_chr)
            magic_str += m_chr
            make_func(my_name + 1, depth + 1, spread, max_depth, stump, loop, t_path=True, t_depth=t_depth)


            if (depth + 1 == t_depth) and FP_MODE:
                t_call = f"\tif (input[{depth}] == '{m_chr}') {{void (*fp)(char* input) = target_{my_name + 1}; fp(input);}}\n"
            else:
                t_call = f"\tif (input[{depth}] == '{m_chr}') {{target_{my_name + 1}(input);}}\n"

    # generate children
    child_lst = []
    child_calls = []
    for i in range(0, children):
        child_name = new_name()
        child_lst.append(child_name)
        m_chr = chr(random.randint(32, 126))
        while (m_chr in magic_chr) or (m_chr == '\\') or (m_chr == '\''):
            m_chr = chr(random.randint(32, 126))
        magic_chr.append(m_chr)
        call = f"\tif (input[{depth}] == '{m_chr}') {{func_{child_name}(input);}}\n"
        child_calls.append(call)
        make_func(child_name, depth + 1, spread, max_depth, stump, loop)

    # decide if loops back to another func (main is never part of a loop)
    loop_roll = random.random()
    loops = True if (loop_roll <= loop and not is_main) else False
    if loops:
        loop_to = random.randint(1, name) if (name > 1) else 1

    # generate function header
    if is_main:
        func_header = f"int main(int argc, char** argv) {{\n"
        # process input
        func_header += f"\tchar* input = argv[1];\n"
        # prevent from crashing if no input
        func_header += f'\tif (argc < 2) {{printf("no input\\n"); return 0;}}\n'
    elif not t_path:
        func_header = f"void func_{my_name}(char* input) {{\n"
    else:
        func_header = f"void target_{my_name}(char* input) {{\n"

    # write out func to tmp-file
    with open("tmp", 'a') as tmp:
        tmp.write(func_header)
        if not is_final:
            if t_path:
                tmp.write(t_call)
            for c in child_calls:
                tmp.write(c)
        if t_path and is_final:
            tmp.write("\t/* CHRASH HERE!!! */\n")
            tmp.write(CRASH)
        if loops:
            tmp.write(f"\tfunc_{loop_to}(input);\n")
        if is_main:
            tmp.write("\treturn 0;\n")
        tmp.write("}\n\n")


# main (duh!)
if __name__ == "__main__":
    # parameters
    spread = [1,5]      # how many brances per node (range for random)
    max_depth = 7       # max depth for decoy brances
    stump = 0.1         # propability for a decoy func to be a leaf before reaching max_depth
    loop = 0.2          # propability for a func to loop to another func
    t_depth = 5         # depth of the target function that contains the crash

    print(f"Creating dungeon...")

    # build code
    make_func(0, 0, spread, max_depth, stump, loop, t_depth=t_depth)

    # write out code
    includes = f"#include <stdlib.h>\n#include <stdio.h>\n\n"
    with open(C_FILE, 'w') as c_file:
        c_file.write(includes)
        c_file.write("/* PROTOTYPES */\n")
        for i in range(1, t_depth + 1):
            c_file.write(f"void target_{i} (char* input);\n")
        for i in range(1, name + 1):
            c_file.write(f"void func_{i} (char* input);\n")
        c_file.write("\n/* FUNCTIONS */\n")
        with open("tmp", 'r') as tmp:
            for line in tmp:
                c_file.write(line)

    print(f"Done.\nDungeon contains {name} decoy functions and {t_depth} target functions (total: {name + t_depth}).")
    # clean up
    os.remove("tmp")

    # write out crashing input
    print(f"Magic string is: {magic_str}")
    with open("crash", 'w') as c:
        c.write(magic_str)