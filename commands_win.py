from __future__ import print_function
import gdb, re, collections
gdb.execute("set pagination off")
gdb.execute("set disassembly-flavor intel")

void_ptr = gdb.lookup_type("void").pointer()

# all fields-->str/None
tuple_examine_expression = collections.namedtuple("tuple_examine_expression", "all address symbol")
hex_plain = re.compile(r"[0-9a-fA-F]+")
hex_number = re.compile(r"0x" + hex_plain.pattern)
hex_number_grouped = re.compile(r"(" + hex_number.pattern + r")")
address_with_symbol = re.compile(r"(" + hex_number_grouped.pattern + r"\s*(<.+>)?)")  # 0x7f3067f1174d <poll+45>\n

def get_registers():
    if str(gdb.parse_and_eval("$rax")) == "void":
        return ["eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp", "eip"]
    else:
        return ["rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp", "rip", "r8", "r9", "r10", "r11", "r12",
                "r13", "r14", "r15"]

def examine_expression(expression):
    try:
        value = gdb.parse_and_eval(expression).cast(void_ptr)
    except Exception as e:
        print(e, "for expression " + expression)
        return tuple_examine_expression(None, None, None)
    result = address_with_symbol.search(str(value))
    return tuple_examine_expression(*result.groups())

# step-and-search regex search_depth
class StepAndSearch(gdb.Command):
    def __init__(self):
        super(StepAndSearch, self).__init__("step-and-search", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        registers = get_registers()
        regex, search_depth = arg.split()
        try:
            compiled_regex = re.compile(regex)
        except:
            print(regex + " is not a valid regex")
            return
        try:
            search_depth = int(search_depth, 0)
        except:
            print(str(search_depth) + " is not a valid number")
            return
        current_inferior=gdb.selected_inferior()
        while True:
            for register in registers:
                try:
                    content=str(gdb.parse_and_eval("$" + register))
                    try:
                        address=int(content,0)
                    except:
                        address=int(re.search("0x[0-9a-fA-F]+", content).group(0),0)
                    dump=bytes(current_inferior.read_memory(address, search_depth))
                except:
                    continue
                if compiled_regex.search(dump):
                    dump = dump.replace(b"\0", b"\1")
                    result = dump.decode("ascii", "ignore")
                    print(result)
                    print(register)
                    return
            gdb.execute("nexti")

class SingleCommandBP(gdb.Breakpoint):
    def __init__(self, spec, command):
        super(SingleCommandBP, self).__init__(spec, gdb.BP_BREAKPOINT, internal = False)
        self.command = command

    def stop (self):
        gdb.execute(self.command)
        # Continue automatically
        return False

"""
snake-solve start_address control_flow bad_boy good_boy good_end
snake-solve 0x7FF7EAED4BB0 0x7FF7EAED4BBC 0x7FF7EAED4C23 0x7FF7EAED4C07 0x7FF7EAED4C17 (Snake+4BB0) (Snake+4BBC) (Snake+4C23) (Snake+4C07) (Snake+4C17)
you can delete the disabled breakpoints afterwards
"""
class SnakeSolve(gdb.Command):
    def __init__(self):
        super(SnakeSolve, self).__init__("snake-solve", gdb.COMMAND_USER)

    def init_iterate(self):
        self.current_inferior=gdb.selected_inferior()
        self.data_init=0
        self.step=0
        self.data=self.data_init
        self.flag=""
        if str(gdb.parse_and_eval("$rax")) == "void":
            self.ip_register="$eip"
        else:
            self.ip_register="$rip"
        self.registers=get_registers()
        self.registers.remove(self.ip_register[1:])

    def invoke(self, arg, from_tty):
        items=arg.split()
        if arg:
            addresses=[int(examine_expression(x).address,16) for x in arg.split()]
            self.start_address, self.control_flow, self.bad_boy, self.good_boy, self.good_end=addresses
            for address in addresses:
                SingleCommandBP("*"+hex(address), "snake-solve")
            self.init_iterate()
        else:  # order is important
            ip=int(str(gdb.parse_and_eval(self.ip_register)).split()[0],0)
            if ip==self.start_address:
                self.save_state()
            if ip==self.control_flow:
                self.set_resources()
            elif ip==self.bad_boy:
                self.iterate_next()
                gdb.execute("set "+self.ip_register+"="+hex(self.start_address))
                self.load_state()
            elif ip==self.good_boy:
                self.level_up()
            elif ip==self.good_end:
                print("the solution is: "+self.flag)
                gdb.execute("disable")

    def save_state(self):
        self.state=[examine_expression("$"+x).address for x in self.registers]

    def load_state(self):
        for x,y in zip(self.registers, self.state):
            gdb.execute("set $"+x+"="+y)

    def iterate_next(self):
        if self.data>255:
            raise Exception("Reached max iteration")
        self.data+=1

    def set_resources(self):
        address=examine_expression("*((char**)$rcx)+0x18+"+str(self.step*2)).address  # [[$rcx]+0x18+step*2]
        self.current_inferior.write_memory(int(address,16), chr(self.data))

    def level_up(self):
        self.flag+=chr(self.data)
        self.step+=1
        self.data=self.data_init

StepAndSearch()
SnakeSolve()
