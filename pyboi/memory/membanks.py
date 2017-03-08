from .mbc0 import MBC0
from .rambank import RAMBank
import logging
log = logging.getLogger(name='membanks')

class MemBanks:
    """
    Represents the memory bank controllers on the game cartridge.

    ...
    Attributes
    ----------
    bank : MemBankController object
        internal MBC in use
    rambank : RamBank
        rambanks for the cartridge

    """
    def __init__(self, cartridge):
        """
        Initialize the mem bank from the ROM.

        ...
        Parameters
        ----------
        cartridge : bytearray
            the ROM to initialize from

        """
        if cartridge[0x147] == 0x0:
            self.rombank = MBC0(cartridge)
        else:
            log.critical('This MBC has not been implemented yet!')
        self.rambank = RAMBank(cartridge[0x149])

    def read(self, address):
        """
        Read a byte from the memory banks.

        ...
        Parameters
        ----------
        addresss : integer
            to read
        """
        if address < 0x8000:
            return self.rombank.read_byte(address)
        elif address < 0xe000:
            return self.rambank.read_byte(address)
        else:
            log.error('Invalid read from membanks!')

    def write(self, byte, address):
        """
        Write a byte to the memory banks.

        ...
        Parameters
        ----------
        byte : int
            to write
        address : int
            to write to
        """
        if address < 0x8000:
            self.rombank.write_byte(byte, address)
        elif address < 0xe000:
            self.rambank.write_byte(byte, address)
        else:
            log.error('Invalid write to membanks!')
