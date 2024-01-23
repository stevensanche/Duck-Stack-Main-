"""
Assembler Phase I for Duck Machine assembly language.

This assembler produces fully resolved instructions,
which may be the input of assembler_phase2.py.
The input of this phase may contain symbolic
addresses, e.g.,
    again:   LOAD  r1,x
             SUB  r1,r0,r2[5]
             JUMP/P  again
    x:  DATA 12

Assembly instruction format with all options is

label: instruction

Both parts are optional:  A label may appear without
an instruction, and an instruction may appear without
a label.

A label is at least one alphabetic letter
followed by any number of letters (of any kind)
and underscore, e.g., My_dog_boo.

An instruction has the following form:

  opcode/predicate  target,src1,src2[disp]

Opcode is required, and should be one of the DM2022
instruction codes (ADD, MOVE, etc).

/predicate is optional.  If present, it should be some
combination of M,Z,P, or V e.g., /NP would be "execute if
not zero".  If /predicate is not given, it is interpreted
as /ALWAYS, which is an alias for /MZPV.

target, src1, and src2 are register numbers (r0,r1, ... r15)

[disp] is optional.  If present, it is a 10 bit
signed integer displacement.  If absent, it is
treated as [0].

The second source register and displacement may be replaced
by a label, e.g.,
    LOAD  r1,x
In an instruction with the pseudo-operation JUMP,
all the registers may be omitted (a target of r15 is implied)
and replaced by a label, e.g.,
    JUMP/Z  again
Instructions with these forms will be translated to fully
resolved instructions, e.g.,
    LOAD r1,r0,r15[14]  #x
    ADD/Z r15,r0,15[-7] #again

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
from typing import Dict, List

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# Configuration constants
ERROR_LIMIT = 5    # Abandon assembly if we exceed this

# Exceptions raised by this module
class SyntaxError(Exception):
    pass


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
    # An instruction that refers to a memory
    # location in place of its source and offset
    # parts.
    MEMOP = auto()
    JUMP = auto()


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

ASM_MEMOP_PAT = re.compile(r""" 
    \s*
    # Optional label
    (
        (?P<label> [a-zA-Z]\w*):
    )?
    \s*
    # The instruction paper
     (?P<opcode>    [a-zA-Z]+)              # Opcode
     (/ (?P<predicate> [A-Z]+) )?           # Predicate (optional)
     \s+
     (?P<target>    r[0-9]+),               # Target register
     (?P<labelref>  [a-zA-Z]\w*)           # Label reference
     
     # optional comment follows # or ;
    (
      \s*
      (?P<comment>[\#;].*)
    )?
    \s*$
    """, re.VERBOSE)

ASM_JUMP_PAT = re.compile(r""" 
    \s*
    # Optional label
    (
      (?P<label> [a-zA-Z]\w*):
    )?
    \s*
    # The instruction proper
    (?P<opcode>    JUMP)                   # Opcode
    (/ (?P<predicate> [A-Z]+) )?           # Predicate (optional)
    \s+
    (?P<labelref>    [a-zA-Z]\w*)               # Target register
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
            (ASM_COMMENT_PAT, AsmSrcKind.COMMENT),
            (ASM_MEMOP_PAT, AsmSrcKind.MEMOP),
            (ASM_JUMP_PAT, AsmSrcKind.JUMP)
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


def value_parse(int_literal: str) -> int:
    """Parse an integer literal that could look like
    42 or like 0x2a
    """
    if int_literal.startswith("0x"):
        return int(int_literal, 16)
    else:
        return int(int_literal, 10)


def transform(lines: list[str]) -> list[str]:
    """
    Transform some assembly language lines, leaving others
    unchanged.
    Initial version:  No changes to any source line.

    Planned version:
       again:   STORE r1,x
                SUB   r1,r0,r0[1]
                JUMP/P  again
                HALT r0,r0,r0
       x:       DATA 0
    should become
       again:   STORE r1,r0,r15[4]   # x
                SUB   r1,r0,r0[1]
                ADD   r15,r0,r15[-2]
                HALT r0,r0,r0
       x:       DATA 0
     """
    address = 0
    transformed = [ ]
    labels = resolve(lines)
    for lnum in range(len(lines)):
        line = lines[lnum].rstrip()
        log.debug(f"Processing line {lnum}: {line}")
        try:
            fields = parse_line(line)

            if fields["kind"] == AsmSrcKind.FULL:
                log.debug("Passing through FULL instruction")
                transformed.append(line)

            elif fields["kind"] == AsmSrcKind.DATA:
                log.debug("Passing through DATA instruction")
                data = f"{fields['label']}: {fields['opcode']} {fields['value']}"
                transformed.append(data)

            elif fields["kind"] == AsmSrcKind.MEMOP:
                fix_optional_fields(fields)
                ref = fields["labelref"]
                mem_addr = labels[ref]
                pc_relative = mem_addr - address
                f = fields
                full = (f"{f['label']}   {f['opcode']}{f['predicate']} " +
                        f" {f['target']},r0,r15[{pc_relative}] #{ref}" +
                        f" {fields['comment']}")
                transformed.append(full)

            elif fields["kind"] == AsmSrcKind.JUMP:
                fix_optional_fields(fields)
                ref = fields["labelref"]
                mem_addr = labels[ref]
                pc_relative = mem_addr - address
                f = fields
                full = (f"ADD{f['predicate']}"+
                    f" r15,r0,r15[{pc_relative}] #{ref}")
                transformed.append(full)

            else:
                log.debug(f"No instruction on line {lnum}: {line}")
                transformed.append(line)
            if fields["kind"] != AsmSrcKind.COMMENT:
                address += 1

        except SyntaxError as e:
            address += 1
            print(f"Syntax error in line {lnum}: {line}", file=sys.stderr)
        except KeyError as e:
            address += 1
            print(f"Unknown word in line {lnum}: {e}", file=sys.stderr)
        except Exception as e:
            address += 1
            print(f"Exception encountered in line {lnum}: {e}", file=sys.stderr)
            sys.exit(1)
    return transformed


def resolve(lines: list[str]) -> dict[str, int]:
    """
    Build table associating labels in the source code
    with addresses.
    """

    labels: dict[str, int] = { }
    address = 0
    for lnum in range(len(lines)):
        line = lines[lnum].rstrip()
        log.debug(f"Processing line {lnum}: {line}")
        try:
            fields = parse_line(line)
            if fields["label"] is not None:
                labels[fields["label"]] = address
            if fields["kind"] != AsmSrcKind.COMMENT:
                address += 1
        except Exception:
            # Just ignore errors here; they will be handled in
            # transform
            pass
    return labels


def fix_optional_fields(fields: Dict[str, str]):
    """Fill in values of optional fields label,
    predicate, and comment, adding the punctuation
    they require.
    """
    if fields.get("label") is None:
        fields["label"] = "     "
    else:
        fields["label"] = fields["label"].strip() + ":"
    if fields.get("predicate") is None:
        fields["predicate"] = "     "
    else:
        fields["predicate"] = "/" + fields["predicate"].strip()
    if fields["comment"] is None:
        fields["comment"] = "   "
    else:
        fields["comment"] = fields["comment"].strip()



def squish(s: str) -> str:
    """Discard initial and final spaces and compress
    all other runs of whitespace to a single space,
    """
    parts = s.strip().split()
    return " ".join(parts)


def cli() -> object:
    """Get arguments from command line"""
    parser = argparse.ArgumentParser(description="Duck Machine Assembler (phase 1)")
    parser.add_argument("sourcefile", type=argparse.FileType('r'),
                            nargs="?", default=sys.stdin,
                            help="Duck Machine assembly code file")
    parser.add_argument("objfile", type=argparse.FileType('w'),
                            nargs="?", default=sys.stdout,
                            help="Transformed assembly language file")
    args = parser.parse_args()
    return args


def main(sourcefile: io.IOBase, objfile: io.IOBase):
    """"Assemble a Duck Machine program"""
    lines = sourcefile.readlines()
    object_code = transform(lines)
    log.debug(f"Object code: \n{object_code}")
    for word in object_code:
        log.debug(f"Instruction word {word}")
        print(word,file=objfile)




