"""
Assembler Phase II for DM2022 assembly language.

This assembler is for fully resolved instructions,
which may be the output of assembler_phase1.py.

Assembly instruction format with all options is 

label: instruction

Labels are resolved (translated into addresses) in
phase I.  In fully resolved assembly code, the input
to this phase of the assembler, they serve
only as documentation.

Both parts are optional:  A label may appear without 
an instruction, and an instruction may appear without 
a label. 

A label is just an alphabetic string, eg.,
  myDogBoo but not Betcha_5_Dollars

An instruction has the following form: 

  opcode/predicate  target,src1,src2[disp]

Opcode is required, and should be one of the Duck Machine
instruction codes (ADD, MOVE, etc).

/predicate is optional.  If present, it should be some 
combination of M,Z,P, or V e.g., /NP would be "execute if
not zero".  If /predicate is not given, it is interpreted
as /ALWAYS, which is an alias for /MZPV.

target, src1, and src2 are register numbers (r0,r1, ... r15)

[disp] is optional.  If present, it is a 10 bit
signed integer displacement.  If absent, it is 
treated as [0]. 

DATA is a pseudo-operation:
   myvar:  DATA   18
indicates that the integer value 18
should be stored at this location, rather than
a Duck Machine instruction.

"""
import io

import context
from instruction_set.instr_format import Instruction, OpCode, CondFlag, NAMED_REGS

import argparse
from enum import Enum, auto
import sys
import re

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# Configuration constants
ERROR_LIMIT = 5    # Abandon assembly if we exceed this

# Exceptions raised by this module
class SyntaxError(Exception):
    pass

###
# The whole instruction line is encoded as a single
# regex with capture names for the parts we might
# refer to. Error messages will be crappy (we'll only
# know that the pattern didn't match, and not why), but 
# we get a very simple match/process cycle.  By creating
# a dict containing the captured fields, we can determine
# which optional parts are present (e.g., there could be
# label without an instruction or an instruction without
# a label).
###


# To simplify client code, we'd like to return a dict with
# the right fields even if the line is syntactically incorrect. 
DICT_NO_MATCH = { 'label': None, 'opcode': None, 'predicate': None,
                      'target': None, 'src1': None, 'src2': None,
                      'offset': None, 'comment': None }


###
# Although the Duck Machine instruction set is very simple, a source
# line can still come in several forms.  Each form (even comments)
# can start with a label.
###

class AsmSrcKind(Enum):
    """Distinguish which kind of assembly language instruction
    we have matched.  Each element of the enum corresponds to
    one of the regular expressions below.
    """
    # Blank or just a comment, optionally
    # with a label
    COMMENT = auto()
    # Fully specified  (all addresses resolved)
    FULL = auto()
    # A data location, not an instruction
    DATA = auto()


# Lines that contain only a comment (and possibly a label).
# This includes blank lines and labels on a line by themselves.
#
ASM_COMMENT_PAT = re.compile(r"""
   \s*
   # Optional label 
   (
     (?P<label> [a-zA-Z]\w*):
   )?
   \s*
   # Optional comment follows # or ; 
   (
     (?P<comment>[\#;].*)
   )?       
   \s*$             
   """, re.VERBOSE)

# Instructions with fully specified fields. We can generate
# code directly from these.
ASM_FULL_PAT = re.compile(r"""
   \s*
   # Optional label 
   (
     (?P<label> [a-zA-Z]\w*):
   )?
   \s*
    # The instruction proper 
    (?P<opcode>    [a-zA-Z]+)           # Opcode
    (/ (?P<predicate> [A-Z]+) )?   # Predicate (optional)
    \s+
    (?P<target>    r[0-9]+),            # Target register
    (?P<src1>      r[0-9]+),            # Source register 1
    (?P<src2>      r[0-9]+)             # Source register 2
    (\[ (?P<offset>[-]?[0-9]+) \])?     # Offset (optional)
   # Optional comment follows # or ; 
   (
     \s*
     (?P<comment>[\#;].*)
   )?       
   \s*$             
   """, re.VERBOSE)

# Defaults for values that ASM_FULL_PAT makes optional
INSTR_DEFAULTS = [ ('predicate', 'ALWAYS'), ('offset', '0') ]

# A data word in memory; not a Duck Machine instruction
#
ASM_DATA_PAT = re.compile(r""" 
   \s* 
   # Optional label 
   (
     (?P<label> [a-zA-Z]\w*):
   )?
   # The instruction proper  
   \s*
    (?P<opcode>    DATA)           # Opcode
   # Optional data value
   \s*
   (?P<value>  (0x[a-fA-F0-9]+)
             | ([0-9]+))?
    # Optional comment follows # or ; 
   (
     \s*
     (?P<comment>[\#;].*)
   )?       
   \s*$             
   """, re.VERBOSE)


# We will try each pattern in turn.  The PATTERNS table
# is to associate each pattern with the kind of instruction
# that each pattern matches.
#
PATTERNS = [(ASM_FULL_PAT, AsmSrcKind.FULL),
            (ASM_DATA_PAT, AsmSrcKind.DATA),
            (ASM_COMMENT_PAT, AsmSrcKind.COMMENT)
            ]

def parse_line(line: str) -> dict:
    """Parse one line of assembly code.
    Returns a dict containing the matched fields,
    some of which may be empty.  Raises SyntaxError
    if the line does not match assembly language
    syntax. Sets the 'kind' field to indicate
    which of the patterns was matched.
    """
    log.debug(f"\nParsing assembler line: '{line}'")
    # Try each kind of pattern
    for pattern, kind in PATTERNS:
        match = pattern.fullmatch(line)
        if match:
            fields = match.groupdict()
            fields["kind"] = kind
            log.debug(f"Extracted fields {fields}")
            return fields
    raise SyntaxError(f"Assembler syntax error in {line}")


def fill_defaults(fields: dict) -> None:
    """Fill in default values for optional fields of instruction"""
    for key, value in INSTR_DEFAULTS:
        if fields[key] == None:
            fields[key] = value


def value_parse(int_literal: str) -> int:
    """Parse an integer literal that could look like
    42 or like 0x2a
    """
    if int_literal.startswith("0x"):
        return int(int_literal, 16)
    else:
        return int(int_literal, 10)


def to_flag(m: str) -> CondFlag:
    """Making a condition code from a mnemonic
    that might be one of the existing codes
    like Z or NEVER or might be a combination
    like PZ.
    """
    if m in [ flag.name for flag in CondFlag ]:
        return CondFlag[m]
    composite = CondFlag.NEVER
    for bitname in m:
        composite = composite | CondFlag[bitname]
    return composite


def instruction_from_dict(d: dict) -> Instruction:
    """Use fields of d to create an Instruction object.
    Raises key_error if a needed field is missing or
    misspelled (e.g., reg10 instead of r10)
    """
    opcode = OpCode[d["opcode"]]
    pred = to_flag(d["predicate"])
    target = NAMED_REGS[d["target"]]
    src1 = NAMED_REGS[d["src1"]]
    src2 = NAMED_REGS[d["src2"]]
    offset = int(d["offset"])
    return Instruction(opcode, pred, target, src1, src2, offset)


def assemble(lines: list[str]) -> list[int]:
    """
    Simple one-pass translation of assembly language
    source code into instructions.  Empty lines and lines
    with only labels and comments are skipped.
    Handles *only* numerical offsets, not symbolic labels.
    For example:
        STORE   r1,r0,r15[8]    # OK, store value of r1 at location pc+8
        ADD/Z   r15,r0,r0[-3]   # OK, jump 3 steps back if zero is in condition code
    but not
        STORE   r1,variable     # cannot use symbolic address of variable
        JUMP/Z  again           # cannot use pseudo-instruction JUMP or symbolic label 'again'
    """
    error_count = 0
    instructions = [ ]
    for lnum in range(len(lines)):
        line = lines[lnum]
        log.debug(f"Processing line {lnum}: {line}")
        try: 
            fields = parse_line(line)
            if fields["kind"] == AsmSrcKind.FULL:
                log.debug("Constructing instruction")
                fill_defaults(fields)
                instr = instruction_from_dict(fields)
                word = instr.encode()
                instructions.append(word)
            elif fields["kind"] == AsmSrcKind.DATA:
                word = value_parse(fields["value"])
                instructions.append(word)
            else:
                log.debug(f"No instruction on line {lnum}: {line}")
        except SyntaxError as e:
            error_count += 1
            print(f"Syntax error in line {lnum}: {line}", file=sys.stderr)
        except KeyError as e:
            error_count += 1
            print(f"Unknown word in line {lnum}: {e}", file=sys.stderr)
        except Exception as e:
            error_count += 1
            print(f"Exception encountered in line {lnum}: {e}", file=sys.stderr)
        if error_count > ERROR_LIMIT:
            print("Too many errors; abandoning", file=sys.stderr)
            sys.exit(1)
    return instructions

def cli() -> object:
    """Get arguments from command line"""
    parser = argparse.ArgumentParser(description="Duck Machine Assembler (pass 2)")
    parser.add_argument("sourcefile", type=argparse.FileType('r'),
                            nargs="?", default=sys.stdin,
                            help="Duck Machine assembly code file")
    parser.add_argument("objfile", type=argparse.FileType('w'),
                            nargs="?", default=sys.stdout, 
                            help="Object file output")
    args = parser.parse_args()
    return args


def main(sourcefile: io.IOBase, objfile: io.IOBase):
    """"Assemble a Duck Machine program"""
    lines = sourcefile.readlines()
    object_code = assemble(lines)
    log.debug(f"Object code: \n{object_code}")
    for word in object_code:
        log.debug(f"Instruction word {word}")
        print(word,file=objfile)

if __name__ == "__main__":
    args = cli()
    main(args.sourcefile, args.objfile)

