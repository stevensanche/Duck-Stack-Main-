"""
Driver (main program) for expression compiler. 
Input is parsed by llparse.py to create an
Expr object.  The 'gen' methods in Expr walk over
the Expr tree and produce assembly code in the
Context object.
"""
import io

import context as path_context # So it doesn't collide with codegen_context
from compiler.llparse import parse, InputError
from compiler.lex import LexicalError
import compiler.codegen_context as codegen_context

import datetime
import argparse
import sys

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def cli() -> object:
    """Get arguments from command line"""
    parser = argparse.ArgumentParser(description="Mallard Compiler")
    parser.add_argument("sourcefile", type=argparse.FileType('r'),
                        help="Source program text")
    parser.add_argument("objfile", type=argparse.FileType('w'),
                        nargs="?", default=sys.stdout,
                        help="Output file for assembly code")
    args = parser.parse_args()
    return args


def main(sourcefile: io.FileIO, objfile: io.IOBase):
    context = codegen_context.Context()
    context.add_line("# Lovingly crafted by the robots of CIS 211")
    context.add_line(f"# {datetime.datetime.now()} from {sourcefile.name}")
    context.add_line("#")
    try:
        exp = parse(sourcefile)
        log.debug(f"Parsed to: {exp}")
        work_register = context.allocate_register()
        exp.gen(context, work_register)
        context.free_register(work_register)
        context.add_line("\tHALT  r0,r0,r0")
        assm = context.get_lines()
        log.debug(f"assm = {assm}")
        for line in assm:
            print(line, file=objfile)
        log.info("#Compilation complete")
    except InputError as e:
        log.warning("Syntax error, bailing")
        log.warning(e)
    except LexicalError as e:
        log.warning("Lexical error, bailing")
    except Exception as e:
        log.warning("Failed!")
        raise e


if __name__ == "__main__":
    args = cli()  # Factored out of main so it can be used as API
    main(args.sourcefile, args.objfile)
