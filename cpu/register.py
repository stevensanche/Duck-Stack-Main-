"""
A Duck Machine register holds a 32 bit integer. 
The Zero register is special: It always holds 0. 
"""


class Register(object):
    """Holds a 32-bit integer"""

    def __init__(self):
        self._value = 0

    def get(self) -> int:
        return self._value

    def put(self, value) -> None:
        self._value = value


class ZeroRegister(Register):
    """A register whose value can never change"""
    def put(self, value) -> None:
        pass

    
