"""Translate and run an assembly language program.
Top-level script chains together assembler phase 1,
assembler phase 2, and CPU simulator
"""
import io

import context
import asm.assembler_phase1 as asm1
import asm.assembler_phase2 as asm2
import cpu.duck_machine as machine

import sys
import argparse
import os.path

def cli():
    """Get arguments from command line"""
    parser = argparse.ArgumentParser(description="Assemble and go")
    parser.add_argument("sourcefile", type=argparse.FileType('r'),
                            nargs="?", default=sys.stdin,
                            help="Duck Machine assembly code file")
    parser.add_argument("-d", "--display", help="Graphical display",
                        action="store_true")
    parser.add_argument("-s", "--step", help="Single step mode",
                        action="store_true")
    args = parser.parse_args()
    return args

def main(source: io.IOBase, display=False, step=False):
    # Create and use temporary files in ../programs/tmp
    this_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    tmp_dir = os.path.abspath(os.path.join(this_dir, "../programs/tmp"))
    # Assembler phase 1
    dasm_path = os.path.join(tmp_dir, "tmp.dasm")
    dasm = open(dasm_path, "w")
    asm1.main(source, dasm)
    dasm.close()
    # Assembler phase 2
    obj_path = os.path.join(tmp_dir, "tmp.obj")
    dasm = open(dasm_path, "r")
    obj = open(obj_path, "w")
    asm2.main(dasm, obj)
    obj.close()
    # Execute in simulator
    obj = open(obj_path, "r")
    machine.main(obj, display=display, single_step=step)


if __name__ == "__main__":
    args = cli()
    main(args.sourcefile, display=args.display, step=args.step)

