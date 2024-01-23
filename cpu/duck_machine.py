"""
Duck Machine model DM2022,
a simulated computer. 

Interprets Duck Machine object code.
(This is a "main program" for the hardware simulation part
of the Duck Machine series of projects.)
"""

import context
from cpu.memory import Memory, MemoryMappedIO
from cpu.cpu import CPU
import cpu.view as view

import argparse
import io

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def cli() -> object:
    """Get arguments from command line"""
    parser = argparse.ArgumentParser(description="Duck Machine Simulator")
    parser.add_argument("objfile", type=argparse.FileType('r'),
                            help="Object file input")
    parser.add_argument("-d", "--display", help="Graphical cpu_display",
                        action="store_true")
    parser.add_argument("-s", "--step", help="Single step mode",
                        action="store_true")
    args = parser.parse_args()
    return args

def load(file: io.IOBase, memory: Memory) -> None:
    addr = 0
    log.debug(f"Loading from address 0")
    for line in file:
        word = int(line)
        log.debug(f"Instruction value {word}")
        memory.put(addr, word)
        log.debug(f"Loaded {word} from address {addr} ")
        addr += 1

def duck_output(addr: int, value: int) -> None:
    print(f"Quack!: {value}")

def duck_input(addr: int) -> int:
    return int(input("Quack! Gimme an int! "))

def main(objfile: io.IOBase, display=False, single_step=False):
    """" Run a Duck Machine program from
    object code file.
    """
    log.debug("Creating the memory")
    mem = MemoryMappedIO(512)
    # We'd like to make it simple to trigger I/O with
    # a single instruction, so it would be good to fit
    # the memory mapped addresses into the offset field.
    # For that, maximum positive value is 511.  We'll
    # reserve addresses 510 and 511 for input and output
    # respectively.
    log.debug("Mapping addresses 510,511 to input and output ports")
    mem.map_address_in(510, duck_input)
    mem.map_address_out(511, duck_output)
    cpu = CPU(mem)
    if display:
        log.debug("Creating a cpu_display")
        cpu_display = view.MachineStateView(cpu, 1200, 800)
    log.debug(f"Loading object file {objfile}")
    load(objfile, mem)
    log.debug(f"Loaded, running from start")
    cpu.run(single_step=single_step)
    print("Halted")
    if display:
      input("Press enter to end")


if __name__ == "__main__":
    args = cli()
    main(args.objfile, display=args.display, single_step=args.step)
