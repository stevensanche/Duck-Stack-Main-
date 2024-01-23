"""Unit tests for bitfield.py"""
import unittest
import context

from instruction_set.bitfield import BitField
from instruction_set.bitfield import sign_extend

class Test_Extract(unittest.TestCase):

    def test_extract_low(self):
        """Extract low 3 bits"""
        low_bits = BitField(0, 3)
        self.assertEqual(low_bits.extract(0b10101010101), 0b101)

    def test_middle_bits(self):
        """Extract 5 bits from the middle of a word"""
        middle_bits = BitField(5,9)
        self.assertEqual(middle_bits.extract(0b1010101101101011), 0b11011)

    def test_insert_low(self):
        """Inserting a few bits in the lowest part of the word. """
        low_bits = BitField(0, 3)
        self.assertEqual(low_bits.insert(15, 0), 15)  # All the bits to 1
        # Slip it in without disturbing higher bits
        self.assertEqual(low_bits.insert(0b1010, 0b1111_0000), 0b1111_1010)


class Test_Sign_Extension(unittest.TestCase):

    def test_extend_positive(self):
        """Sign extension of a positive number doesn't change it.  Note high
        bit in field must be zero.  7 is a positive number in a 3-bit field,
        but a (different) negative number in a 3-bit field.
        """
        self.assertEqual(sign_extend(7,4), 7)
        self.assertNotEqual(sign_extend(7,3), 7)
        self.assertTrue(sign_extend(7,3) < 0)

    def test_extend_negative(self):
        """For negative numbers, sign extension restores the high bits"""
        chunk = (-3) & 0b111
        self.assertEqual(sign_extend(chunk,3), -3)


class Test_Signed_Extraction(unittest.TestCase):

    def test_extract_neg(self):
        bitfield = BitField(2,4)
        field_bits = 0b_101_111_10  # the 111 part is what we want to extract
        self.assertEqual(bitfield.extract_signed(field_bits), -1)

    def test_extract_pos(self):
        bitfield = BitField(2,4)
        field_bits = 0b_101_011_10  # the 011 part is what we want to extract
        self.assertEqual(bitfield.extract_signed(field_bits), 3)


class Test_Signed_Insert(unittest.TestCase):

    def test_insert_neg(self):
        bitfield = BitField(3, 5)
        packed = bitfield.insert(-1, 0)
        self.assertEqual(packed, 0b000_111_000)
        unpacked = bitfield.extract_signed(packed)
        self.assertEqual(unpacked, -1)