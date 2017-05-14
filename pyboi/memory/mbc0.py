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
    ram : RAMBank object
        the ram for the cartridge
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
        self.ram = RAMBank(cartridge[0x149])

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
        elif address < 0xfdff:
            return self.ram.read_byte(address)
        else:
            log.critical('INVALID READ @ ' + hex(address))
            return 0
        

    def write_byte(self, byte, address):
        """
        Write a byte to mbc0. Does nothing if in rom,
        if ram byte writes to ram
        """
        if address < 0x8000:
            pass
        elif address < 0xfdff:
            self.ram.write_byte(byte, address)
        else:
            log.critical('INVALID WRITE @ ' + hex(address))

