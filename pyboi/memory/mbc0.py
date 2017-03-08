from .rambank import RAMBank
import logging
log = logging.getLogger('mbc0')

class MBC0:
    """
    Represents NO rom banking.

    ...
    Attributes
    ----------
    rom : bytearray
        the 32kb of ROM from the cartridge
    """
    def __init__(self, cartridge):
        """
        Initialize MBC0.

        ...
        Parameters
        ----------
        cartridge : bytearray
            the ROM to initialize from

        """
        self.rom = cartridge

    def read_byte(self, address):
        """
        Read a byte from mbc0.
        
        ...
        Parameters
        ----------
        address : int
            to read

        """
        if address < 0x8000 and address >= 0:
            return self.rom[address]
        
