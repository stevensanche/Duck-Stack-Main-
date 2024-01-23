"""
Name: Steven Sanchez-Jimenez
CS 211, Project: Duck Machine CPU
February 14, 2023,
Resources: In-class tools
"""


"""A bit field is a range of binary digits within an
unsigned integer.   Bit 0 is the low-order bit,
with value 1 = 2^0.  Bit 31 is the high-order bit, 
with value 2^31. 

A bitfield object is an aid to encoding and decoding 
instructions by packing and unpacking parts of the 
instruction in different fields within individual 
instruction words. 
"""

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.setLevel(logging.INFO)

WORD_SIZE = 32


class BitField(object):
    """A BitField object extracts specified
    bitfields from an integer.
    """
    def __init__(self, from_bit: int, to_bit: int) -> None:
        """Tool for  extracting bits
        from_bit ... to_bit, where 0 is the low-order
        bit and 31 is the high-order bit of an unsigned
        32-bit integer. For example, the low-order 4 bits
        could be represented by from_bit=0, to_bit=3.
        """
        assert 0 <= from_bit < WORD_SIZE
        assert from_bit <= to_bit <= WORD_SIZE
        self.from_bit = from_bit
        self.to_bit = to_bit

        self.mask = (1 << (to_bit - from_bit + 1)) - 1

    def extract(self, word: int) -> int:
        """Extract the bitfield and return it in the
        low-order bits.  For example, if we are extracting
        bits 3..5, the result will be an
        integer between 0 and 7 (0b000 to 0b111).
        """
        shift = self.from_bit
        value = (word >> shift) & self.mask
        return value

    def insert(self, value: int, word: int) -> int:
        """Insert value, which should be in the low order
         bits and no larger than the bitfield, into the
         bitfield, which should be zero before insertion.
         Returns the combined value.
         Example: BitField(3,5).insert(0b101, 0b110) == 0b101110
         """
        mask = ((1 << (self.to_bit - self.from_bit + 1)) - 1) << self.from_bit
        return (word & ~mask) | ((value << self.from_bit) & mask)

        """
        shift = value << self.from_bit
        val = shift & self.mask
        mask = word
        mask2 = not(self.mask << self.from_bit)
        mask3 = mask + mask2
        result = mask3 | val
        return result
        """

    def extract_signed(self, word: int) -> int:
        """Extract bits in bitfield as a signed integer."""
        bits = self.to_bit - self.from_bit + 1
        sign_bit = self.from_bit + bits - 1
        mask = (1 << bits) - 1
        value = (word >> self.from_bit) & mask
        if value & (1 << (bits - 1)):
            # If the most significant bit is 1, the value is negative
            return -((1 << bits) - value)
        else:
            return value


def sign_extend(field: int, width: int) -> int:
    """Interpret field as a signed integer with width bits.
    If the sign bit is zero, it is positive.  If the sign bit
    is negative, the result is sign-extended to be a negative
    integer in Python.
    width must be 2 or greater. field must fit in width bits.
    # Examples:
    Suppose we have a 3 bit field, and the field
    value is 0b111 (7 decimal).  Since the high
    bit is 1, we should interpret it as
    -2^2 + 2^1  + 2^0, or -4 + 3 = -1

    Suppose we have the same value, decimal 7 or
    0b0111, but now it's in a 4 bit field.  In thata
    case we should interpret it as 2^2 + 2^1 + 2^0,
    or 4 + 2 + 1 = 7, a positive number.
    """
    assert width > 1
    assert field >= 0
    assert field < 1 << width + 1
    sign_bit = 1 << width - 1  # will have form 1000... for width of field
    mask = sign_bit - 1         # will have form 0111... for width of field
    if field & sign_bit:
        # It's negative; sign extend it
        extended = (field & mask) - sign_bit
        return extended
    else:
        return field


