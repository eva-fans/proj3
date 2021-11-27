#!/usr/bin/python3

"""
CS-UY 2214
Jeff Epstein
Starter code for E20 cache simulator
simcache.py
"""

from collections import namedtuple
import re
import argparse

Constants = namedtuple("Constants",["NUM_REGS", "MEM_SIZE", "REG_SIZE"])
constants = Constants(NUM_REGS = 8, 
                      MEM_SIZE = 2**13,
                      REG_SIZE = 2**16)

def sign_extend(num,old_bits,bits):
    num=num%2**old_bits
    signed_bit=num&2**(old_bits-1)
    if signed_bit!=0:
        for i in range(old_bits,bits):
            num=num|2**i
    return num

def print_state(pc, regs, memory, memquantity):
    """
    Prints the current state of the simulator, including
    the current program counter, the current register values,
    and the first memquantity elements of memory.
    sig: int -> list(int) -> list(int) - int -> NoneType
    """
    print("Final state:")
    print("\tpc="+format(pc,"5d"))
    for reg, regval in enumerate(regs):
        print(("\t$%s=" % reg)+format(regval,"5d"))
    line = ""
    for count in range(memquantity):
        line += format(memory[count], "04x")+ " "
        if count % 8 == 7:
            print(line)
            line = ""
    if line != "":
        print(line)

class Block:
    def __init__(self,size,signal):
        self.size=size
        self.signal=signal
        self.mem=[0 for i in range(0,size)]

    def getMem(self,address):
        address=address%constants.MEM_SIZE
        value=self.mem[address]%constants.REG_SIZE
        return value

    def setMem(self,address,value):
        address=address%constants.MEM_SIZE
        value=value%constants.REG_SIZE
        self.mem[address]=value

class Cache:
    def __init__(self,name,size,assoc,blocksize):
        self.name=name
        self.size=size
        self.assoc=assoc
        self.blocksize=blocksize
        self.ngroup=size/(assoc*blocksize)
        self.mem=[ [] for i in range(0,self.group)]
    
    # return (hit,value)
    def read(self,mem_addr):
        hit=False # True if cache hits
        value=0
        group=mem_addr/self.blocksize%(1<<self.ngroup) # calculate the group number by memory address
        signal=mem_addr/self.blocksize/(1<<self.ngroup) # calculate the signal by memory address
        offset=mem_addr%self.blocksize # calculate cache block offset
        for i in range(0,len(self.mem[group])):
            if self.mem[group][i].signal == signal: # find the correct cache block
                hit=True # update hitting status
                value=self.mem[group][i].getMem(offset) # get the value of word
                # move the block to the list top
                temp=self.mem[group][i]
                self.mem[group].pop(i)
                self.mem[group].insert(0,temp)
                break
        return (hit,value)
    
    # return hit
    def write(self,mem_addr,value):
        hit=False # True if cache hits
        group=mem_addr/self.blocksize%(1<<self.ngroup) # calculate the group number by memory address
        signal=mem_addr/self.blocksize/(1<<self.ngroup) # calculate the signal by memory address
        offset=mem_addr%self.blocksize # calculate cache block offset
        for i in range(0,len(self.mem[group])):
            if self.mem[group][i].signal == signal: # find the correct cache block
                hit=True # update hitting status
                self.mem[group][i].setMem(offset,value)
                # move the block to the list top
                temp=self.mem[group].pop(i)oool.;//
                self.mem[group].insert(0,temp)
                break
        return hit

class Machine:
    def __init__(self,cache_config):
        self.gpregs=[ 0 for i in range(0,constants.NUM_REGS) ] # general-purpose registers
        self.mem=[0 for i in range(0,constants.MEM_SIZE)] # memory of machine
        self.pc=0 # program counter
        self.running=False
        self.log=[]
        if cache_config is None:
            self.cache=[]
        elif len(cache_config)==4:
            self.cache=[Cache(cache_config[0:4])]
        elif len(cache_config)==8:
            self.cache=[Cache(cache_config[0:4]), Cache(cache_config[4:8])]
        else:
            raise Exception("Invalid cache config")
        
    def getMem(self,address):
        address=address%constants.MEM_SIZE
        value=self.mem[address]%constants.REG_SIZE
        return value
    def setMem(self,address,value):
        address=address%constants.MEM_SIZE
        value=value%constants.REG_SIZE
        self.mem[address]=value
    def getGpRegs(self,reg_number):
        reg_number=reg_number%constants.NUM_REGS
        value=self.gpregs[reg_number]%constants.REG_SIZE
        return value
    def setGpRegs(self,reg_number,value):
        reg_number=reg_number%constants.NUM_REGS
        value=value%constants.REG_SIZE
        self.gpregs[reg_number]=value
    def excute_instr(self): # excute one instruction
        instr=self.getMem(self.pc) # get the instruction
        opcode=(instr>>13)%(1<<3)
        instr_jump=False
        jump_address=0
        if opcode==0: # instructions with three register arguments
            subopcode=instr%(1<<4)
            regSrcA=(instr>>10)%(1<<3)
            regSrcB=(instr>>7)%(1<<3)
            regDst=(instr>>4)%(1<<3)
            if subopcode==0: # add instruction
                self.setGpRegs(regDst,self.getGpRegs(regSrcA)+self.getGpRegs(regSrcB))
            elif subopcode==1: # sub instruction
                self.setGpRegs(regDst,self.getGpRegs(regSrcA)-self.getGpRegs(regSrcB))
            elif subopcode==2: # and instruction
                self.setGpRegs(regDst,self.getGpRegs(regSrcA)&self.getGpRegs(regSrcB))
            elif subopcode==3: # or instruction
                self.setGpRegs(regDst,self.getGpRegs(regSrcA)|self.getGpRegs(regSrcB))
            elif subopcode==4: #  setting $regDst to 1 if $regSrcA is less than $regSrcB, and to 0 otherwise
                if self.getGpRegs(regSrcA)<self.getGpRegs(regSrcB):
                    self.setGpRegs(regDst,1)
                else:
                    self.setGpRegs(regDst,0)
            elif subopcode==8:
                instr_jump=True
                jump_address=self.getGpRegs(regSrcA)
            else:
                print("undefined instruction")
                exit(1)
        elif opcode==0x7: # Compares the value of $regSrc with sign-extended imm, setting $regDst to 1 if $regSrc is less than imm, and to 0 otherwise
            regSrc=(instr>>10)%(1<<3)
            regDst=(instr>>7)%(1<<3)
            imm=instr%(1<<7)
            imm=sign_extend(imm,7,16)
            if self.getGpRegs(regSrc)<imm:
                self.setGpRegs(regDst,1)
            else:
                self.setGpRegs(regDst,0)
        elif opcode==0x4: # Calculates a memory pointer by summing the signed number imm and the value $regAddr, and loads the value from that address, storing it in $regDst.
            regAddr=(instr>>10)%(1<<3)
            regDst=(instr>>7)%(1<<3)
            imm=instr%(1<<7)
            imm=sign_extend(imm,7,16)
            value=self.getMem(self.getGpRegs(regAddr)+imm)
            self.setGpRegs(regDst,value)
        elif opcode==0x5: # Calculates a memory pointer by summing the signed number imm and the value $regAddr, and stores the value in $regSrc to that memory address
            regAddr=(instr>>10)%(1<<3)
            regSrc=(instr>>7)%(1<<3)
            imm=instr%(1<<7)
            imm=sign_extend(imm,7,16)
            value=self.getGpRegs(regSrc)
            self.setMem(self.getGpRegs(regAddr)+imm,value)
        elif opcode==0x6: # Compares the value of $regA with $regB. If the values are equal, jumps to the memory address identified by the address imm, which is encoded as the signed number rel_imm
            regA=(instr>>10)%(1<<3)
            regB=(instr>>7)%(1<<3)
            rel_imm=instr%(1<<7)
            rel_imm=sign_extend(rel_imm,7,16)
            regA_value=self.getGpRegs(regA)
            regB_value=self.getGpRegs(regB)
            if regA_value==regB_value:
                imm=self.pc+1+rel_imm
                instr_jump=True
                jump_address=imm
        elif opcode==0x1: # Add immediate
            regSrc=(instr>>10)%(1<<3)
            regDst=(instr>>7)%(1<<3)
            imm=instr%(1<<7)
            imm=sign_extend(imm,7,16)
            self.setGpRegs(regDst,self.getGpRegs(regSrc)+imm)
        elif opcode==0x2: # jump
            imm=instr%(1<<13)
            instr_jump=True
            jump_address=imm
        elif opcode==0x3: # Jump and link
            imm=instr%(1<<13)
            self.setGpRegs(7,self.pc+1)
            instr_jump=True
            jump_address=imm
        else:
            print("undefined instruction")
            exit(1)
        
        if instr_jump:
            if jump_address==self.pc: # halt
                self.running=False
            else:
                self.pc=jump_address%constants.MEM_SIZE
        else:
            self.pc=(self.pc+1)%constants.MEM_SIZE
    
    def start(self):
        self.running=True
        while(self.running):
            self.excute_instr()

def load_machine_code(machine_code, mem):
    """
    Loads an E20 machine code file into the list
    provided by mem. We assume that mem is
    large enough to hold the values in the machine
    code file.
    sig: list(str) -> list(int) -> NoneType
    """
    machine_code_re = re.compile("^ram\[(\d+)\] = 16'b(\d+);.*$")
    expectedaddr = 0
    for line in machine_code:
        match = machine_code_re.match(line)
        if not match:
            raise ValueError("Can't parse line: %s" % line)
        addr, instr = match.groups()
        addr = int(addr,10)
        instr = int(instr,2)
        if addr != expectedaddr:
            raise ValueError("Memory addresses encountered out of sequence: %s" % addr)
        if addr >= len(mem):
            raise ValueError("Program too big for memory")
        expectedaddr += 1
        mem[addr] = instr

def print_cache_config(cache_name, size, assoc, blocksize, num_lines):
    """
    Prints out the correctly-formatted configuration of a cache.

    cache_name -- The name of the cache. "L1" or "L2"

    size -- The total size of the cache, measured in memory cells.
        Excludes metadata

    assoc -- The associativity of the cache. One of [1,2,4,8,16]

    blocksize -- The blocksize of the cache. One of [1,2,4,8,16,32,64])

    sig: str, int, int, int, int -> NoneType
    """

    summary = "Cache %s has size %s, associativity %s, " \
        "blocksize %s, lines %s" % (cache_name,
        size, assoc, blocksize, num_lines)
    print(summary)

def print_log_entry(cache_name, status, pc, addr, line):
    """
    Prints out a correctly-formatted log entry.

    cache_name -- The name of the cache where the event
        occurred. "L1" or "L2"

    status -- The kind of cache event. "SW", "HIT", or
        "MISS"

    pc -- The program counter of the memory
        access instruction

    addr -- The memory address being accessed.

    line -- The cache line or set number where the data
        is stored.

    sig: str, str, int, int, int -> NoneType
    """
    log_entry = "{event:8s} pc:{pc:5d}\taddr:{addr:5d}\t" \
        "line:{line:4d}".format(line=line, pc=pc, addr=addr,
            event = cache_name + " " + status)
    print(log_entry)

def main():
    parser = argparse.ArgumentParser(description='Simulate E20 cache')
    parser.add_argument('filename', help=
        'The file containing machine code, typically with .bin suffix')
    parser.add_argument('--cache', help=
        'Cache configuration: size,associativity,blocksize (for one cache) '
        'or size,associativity,blocksize,size,associativity,blocksize (for two caches)')
    cmdline = parser.parse_args()

    if cmdline.cache is not None:
        parts = cmdline.cache.split(",")
        if len(parts) == 3:
            [L1size, L1assoc, L1blocksize] = [int(x) for x in parts]
            machine=Machine(["L1", L1size, L1assoc, L1blocksize])
            # TODO: execute E20 program and simulate one cache here
        elif len(parts) == 6:
            ["L2", L1size, L1assoc, L1blocksize, "L2", L2size, L2assoc, L2blocksize] = \
                [int(x) for x in parts]
            machine=Machine([L1size, L1assoc, L1blocksize, L2size, L2assoc, L2blocksize])
            # TODO: execute E20 program and simulate two caches here
        else:
            raise Exception("Invalid cache config")
    
    machine=Machine(None)

    with open(cmdline.filename) as file:
        machine_code=file.readlines() # TODO: your code here. Load file and parse using load_machine_code
        load_machine_code(machine_code,machine.mem)
    
    # TODO: your code here. Do simulation.
    machine.start() # turn the machine on



if __name__ == "__main__":
    main()
#ra0Eequ6ucie6Jei0koh6phishohm9