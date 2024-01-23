"""Test cases for the binary encoding of
instructions.
"""

import context
from instruction_set.instr_format import *
import unittest


class TestCondCodes(unittest.TestCase):
    """Condition flags are essentially like single bit bitfields"""

    def test_combine_flags(self):
        non_zero = CondFlag.P | CondFlag.M
        self.assertEqual(str(non_zero), "MP")
        positive = CondFlag.P
        self.assertEqual(str(positive), "P")
        self.assertEqual(str(CondFlag.ALWAYS), "ALWAYS")
        self.assertEqual(str(CondFlag.NEVER), "NEVER")
        # We test overlap of two CondFlag values using bitwise AND
        self.assertTrue(positive & non_zero)
        zero = CondFlag.Z
        self.assertFalse(zero & non_zero)


class TestInstructionString(unittest.TestCase):
    """Check that we can print Instruction objects like assembly language"""

    def test_str_predicated_MUL(self):
        instr = Instruction(OpCode.MUL, CondFlag.P | CondFlag.Z,
                        NAMED_REGS["r1"], NAMED_REGS["r3"], NAMED_REGS["pc"], 42)
        self.assertEqual("MUL/ZP   r1,r3,r15[42]", str(instr))

    def test_str_always_ADD(self):
        """Predication is not printed for the common value of ALWAYS"""
        instr = Instruction(OpCode.ADD, CondFlag.ALWAYS,
                            NAMED_REGS["zero"], NAMED_REGS["pc"], NAMED_REGS["r15"], 0)
        self.assertEqual("ADD   r0,r15,r15[0]", str(instr))


class TestDecode(unittest.TestCase):
    """Encoding and decoding should be inverses"""
    def test_encode_decode(self):
        instr = Instruction(OpCode.SUB, CondFlag.M | CondFlag.Z, NAMED_REGS["r2"], NAMED_REGS["r1"], NAMED_REGS["r3"], -12)
        word = instr.encode()
        text = str(decode(word))
        self.assertEqual(text, str(instr))


if __name__ == "__main__":
    unittest.main()