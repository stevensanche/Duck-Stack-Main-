"""
Instruction format for the Duck Machine 2022 (DM2022),
a simulated computer modeled loosely on the ARM processor
found in many cell phones, the Raspberry Pi, and
(with modifications) recent models of Apple Macintosh.

Instruction words are unsigned 32-bit integers
with the following fields (from high-order to low-order bits).
All are unsigned except offset, which is a signed value in
range -2^11 to 2^11 - 1.

See docs/duck_machine.md for details.
"""

import context  # Search starting at project root
from instruction_set.bitfield import BitField

from enum import Enum, Flag

#  The field bit positions
reserved = BitField(31, 31)
op_field = BitField(26, 30)
cond_field = BitField(22, 25)
reg_target_field = BitField(18, 21)
reg_src1_field = BitField(14, 17)
reg_src2_field = BitField(10, 13)
offset_field = BitField(0, 9)


# The following operation codes control both the ALU and some
# other parts of the CPU.
# ADD, SUB, MUL, DIV, SHL, SHR are ALU-only operations
# HALT, LOAD, STORE involve other parts of the CPU


# Registers are numbered from 0 to 15, and have names
# like r3, r15, etc.  Two special registers have additional
# names:  r0 is called 'zero' because on the DM2022 it always
# holds value 0, and r15 is called 'pc' because it is used to
# hold the program counter.
#
NAMED_REGS = {
    "r0": 0, "zero": 0,
    "r1": 1, "r2": 2, "r3": 3, "r4": 4, "r5": 5, "r6": 6, "r7": 7, "r8": 8,
    "r9": 9, "r10": 10, "r11": 11, "r12": 12, "r13": 13, "r14": 14,
    "r15": 15, "pc": 15
    }


class OpCode(Enum):
    """The operation codes specify what the CPU and ALU should do."""
    # CPU control (beyond ALU)
    HALT = 0    # Stop the computer simulation (in Duck Machine project)
    LOAD = 1    # Transfer from memory to register
    STORE = 2   # Transfer from register to memory
    # ALU operations
    ADD = 3     # Addition
    SUB = 5     # Subtraction
    MUL = 6     # Multiplication
    DIV = 7     # Integer division (like // in Python)


class CondFlag(Flag):
    """The condition mask in an instruction and the format
    of the condition code register are the same, so we can
    logically and them to predicate an instruction.
    """
    M = 1  # Minus (negative)
    Z = 2  # Zero
    P = 4  # Positive
    V = 8  # Overflow (arithmetic error, e.g., divide by zero)
    NEVER = 0
    ALWAYS = M | Z | P | V

    def __str__(self):
        """
        If the exact combination has a name, we return that.
        Otherwise, we combine bits, e.g., ZP for non-negative.
        """
        for i in CondFlag:
            if i is self:
                return i.name
        # No exact alias; give name as sequence of bit names
        bits = []
        for i in CondFlag:
            # The following test is designed to exclude
            # the special combinations 'NEVER' and 'ALWAYS'
            masked = self & i
            if masked and masked is i:
                bits.append(i.name)
        return "".join(bits)


# A complete DM2022 instruction word, in its decoded form.  In
# memory an instruction is just an int.  Before executing an instruction,
# we decode it into an Instruction object so that we can more easily
# interpret its fields.
#
class Instruction(object):
    """An instruction is made up of several fields, which
    are represented here as object fields.
    """

    def __init__(self, op: OpCode, cond: CondFlag,
                     reg_target: int, reg_src1: int,
                     reg_src2: int,
                     offset: int):
        """Assemble an instruction from its fields. """
        self.op = op
        self.cond = cond
        self.reg_target = reg_target
        self.reg_src1 = reg_src1
        self.reg_src2 = reg_src2
        self.offset = offset
        return

    def __str__(self):
        """String representation looks something like assembly code"""
        if self.cond is CondFlag.ALWAYS:
            pred = ""
        else:
            pred = f"/{self.cond}"

        return (f"{self.op.name}{pred}   "
             +  f"r{self.reg_target},r{self.reg_src1},r{self.reg_src2}[{self.offset}]")

    def encode(self) -> int:
        """Encode instruction as 32-bit integer"""
        word = 0
        word = offset_field.insert(self.offset, word)
        word = reg_src2_field.insert(self.reg_src2, word)
        word = reg_src1_field.insert(self.reg_src1, word)
        word = reg_target_field.insert(self.reg_target, word)
        word = cond_field.insert(self.cond.value, word)
        word = op_field.insert(self.op.value, word)
        return word

#  Interpret an integer (memory word) as an instruction.
#  This is the decode part of the fetch/decode/execute cycle of the CPU.
#


def decode(word: int) -> Instruction:
    """Decode a memory word (32 bit int) into a new Instruction"""
    op = op_field.extract(word)
    cond = cond_field.extract(word)
    reg_target = reg_target_field.extract(word)
    reg_src1 = reg_src1_field.extract(word)
    reg_src2 = reg_src2_field.extract(word)
    offset = offset_field.extract_signed(word)
    return Instruction(OpCode(op),
                       CondFlag(cond),
                       reg_target,
                       reg_src1,
                       reg_src2,
                       offset)




