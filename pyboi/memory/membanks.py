from .mbc0 import MBC0
from .mbc1 import MBC1
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
            self.bank = MBC0(cartridge)
            log.info("MBC0")
        elif cartridge[0x147] >= 0x1 and cartridge[0x147] <= 0x3:
            self.bank = MBC1(cartridge)
            log.info("MBC1")
        else:
            log.critical('MBC NOT IMPLEMENTED: '  + str(cartridge[0x147]))
            quit() #just stop

    def read(self, address):
        """
        Read a byte from the memory banks.

        ...
        Parameters
        ----------
        addresss : integer
            to read
        """
        if address < 0xe000:
            return self.bank.read_byte(address)
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
        if address < 0xe000:
            self.bank.write_byte(byte, address)
        else:
            log.error('Invalid write to membanks!')
