from .mbc0 import MBC0
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
        else:
            log.critical('This MBC has not been implemented yet!')

    def read(self, address):
        """
        Read a byte from the memory banks.

        ...
        Parameters
        ----------
        addresss : integer
            to read

        """
        return self.bank.read_byte(address)
