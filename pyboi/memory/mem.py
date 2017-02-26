import os.path
import logging
from .membanks import MemBanks
log = logging.getLogger(name='memory')

class Memory:
    """
    Represents the memory of the GB.

    ...
    Attributes
    ----------
    membanks : MemBank()
        represents the following areas of memory
        0x0000 - 0x7fff : ROMBANKS
        0x8000 - 0xdfff : RAM + RAM banks
    oam : bytearray
        sprite attribute table
        0xfe00 - 0xfe9f
    ioports : bytearray
        0xff00 - 0xff7f
        I/O ports
    hram : bytearray
        0xff80 - 0xfffe 
        high ram

    """
    def __init__(self):
        self.membanks = None
        self.oam = bytearray(0xa0)
        self.ioports = bytearray(0x80)
        self.hram = bytearray(0x80)

    def load_rom(self, rom):
        """
        Load a rom from file into memory.

        ...
        Parameters
        ----------
        rom : string
            path to rom to load

        Returns
        -------
        boolean
            False on failure, or True on success
        NOTE: Logs an appropriate error on Failure

        """
        if not os.path.isfile(rom):
            log.critical('rom file can not be opened')
            return False
        with open(rom, 'rb') as f:
            # this puts entire rom in RAM, but
            # roms are quite small
            self.membanks = MemBanks(bytearray(f.read()))
        return True

    def read(self, address):
        """
        Read a byte from memory

        ...
        Parameters
        ----------
        address : integer
            to read

        """
        if address < 0:
            log.error('negative address read!')
        elif address < 0xdfff:
            return self.membanks.read(address)

    def write(self, byte, address):
        """
        Write a byte to memory.

        ...
        Parameters
        ----------
        byte : int
            byte to write
        address : int
            address to write to

        """
        pass

    
