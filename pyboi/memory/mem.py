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
        0x0 - 0xdfff

    """
    def __init__(self):
        self.membanks = None

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
            log.error('rom file can not be opened')
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
            log.critical('negative address read!')
        elif address < 0x8000:
            return self.membanks.read(address)



    def load_save(self, save_name):
        print("loading save!")
    
