import gdb, re

gdb.execute("set pagination off")
gdb.execute("set disassembly-flavor intel")


def get_mem_file():
    return "/proc/" + str(gdb.selected_inferior().pid) + "/mem"


def get_registers():
    if str(gdb.parse_and_eval("$rax")) == "void":
        return ["eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp", "eip"]
    else:
        return ["rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp", "rip", "r8", "r9", "r10", "r11", "r12",
                "r13", "r14", "r15"]


# usage: step-and-search regex search_depth
class StepAndSearch(gdb.Command):
    def __init__(self):
        super(StepAndSearch, self).__init__("step-and-search", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        registers = get_registers()
        regex, search_depth = arg.split()
        try:
            compiled_regex = re.compile(bytes(regex, "ascii"))
        except:
            print(regex + " is not a valid regex")
            return
        mem_file = get_mem_file()
        try:
            search_depth = int(search_depth, 0)
        except:
            print(str(search_depth) + " is not a valid number")
            return
        while True:
            for register in registers:
                mem_handle = open(mem_file, "rb")
                try:
                    mem_handle.seek(int(gdb.parse_and_eval("$" + register)))
                    dump = mem_handle.read(search_depth)
                except:
                    continue
                if compiled_regex.search(dump):
                    dump = dump.replace(b"\0", b"\1")
                    result = dump.decode("ascii", "ignore")
                    print(result)
                    print(register)
                    return
            gdb.execute("nexti")


StepAndSearch()
