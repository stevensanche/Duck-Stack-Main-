import context
from cpu.cpu import *
import unittest


class TestALU(unittest.TestCase):
    """Simple smoke test of each ALU op"""

    def test_each_op(self):
        alu = ALU()
        # The main computational ops
        # Addition  (Overflow is not modeled)
        self.assertEqual(alu.exec(OpCode.ADD, 5, 3), (8, CondFlag.P))
        self.assertEqual(alu.exec(OpCode.ADD, -5, 3), (-2, CondFlag.M))
        self.assertEqual(alu.exec(OpCode.ADD, -10, 10), (0, CondFlag.Z))
        # Subtraction (Overflow is not modeled)
        self.assertEqual(alu.exec(OpCode.SUB, 5, 3), (2, CondFlag.P))
        self.assertEqual(alu.exec(OpCode.SUB, 3, 5), (-2, CondFlag.M))
        self.assertEqual(alu.exec(OpCode.SUB, 3, 3), (0, CondFlag.Z))
        # Multiplication (Overflow is not modeled)
        self.assertEqual(alu.exec(OpCode.MUL, 3, 5), (15, CondFlag.P))
        self.assertEqual(alu.exec(OpCode.MUL, -3, 5), (-15, CondFlag.M))
        self.assertEqual(alu.exec(OpCode.MUL, 0, 22), (0, CondFlag.Z))
        # Division (can overflow with division by zero
        self.assertEqual(alu.exec(OpCode.DIV, 5, 3), (1, CondFlag.P))
        self.assertEqual(alu.exec(OpCode.DIV, 12, -3), (-4, CondFlag.M))
        self.assertEqual(alu.exec(OpCode.DIV, 3, 4), (0, CondFlag.Z))
        self.assertEqual(alu.exec(OpCode.DIV, 12, 0), (0, CondFlag.V))
        #
        # For other ops, we just want to make sure they have table
        # entries and perform the right operation. Condition code is returned but not used
        self.assertEqual(alu.exec(OpCode.LOAD, 12, 13), (25, CondFlag.P))
        self.assertEqual(alu.exec(OpCode.STORE, 27, 13), (40, CondFlag.P))
        self.assertEqual(alu.exec(OpCode.HALT, 99, 98), (0, CondFlag.Z))


if __name__ == "__main__":
    unittest.main()