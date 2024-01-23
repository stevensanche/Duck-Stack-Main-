"""
An interpreter for the mallard language,
a very small programming language with
integers as the only data type.
The mallard interpreter should have almost
the same behavior as a compiled
mallard program executing on a duck machine.
"""

import io

import context as path_context # So it doesn't collide with codegen_context
from compiler.llparse import parse

import argparse
import sys

import logging

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def cli() -> object:
    """Get arguments from command line"""
    parser = argparse.ArgumentParser(description="Mallard Language Interpreter")
    parser.add_argument("sourcefile", type=argparse.FileType('r'),
                        help="Source program text")
    parser.add_argument("outfile", type=argparse.FileType('w'),
                        nargs="?", default=sys.stdout,
                        help="Output file for assembly code")
    args = parser.parse_args()
    return args

# Note we have *not* factored cli() out of the main interpreter,
# because the interpreter can't be combined with other stages
# in the translation and exection pipeline.
#
def main():
    args = cli()
    try:
        exp = parse(args.sourcefile)
        log.debug(repr(exp))
        exp.eval()
        print("#Interpretation complete")
    except Exception as e:
        print("Failed!")
        print(e)
        raise e


if __name__ == "__main__":
    main()
