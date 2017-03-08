import logging
log = logging.getLogger(name='rambanks')

class RAMBank:
    """
    Represents the optional RAM banks in the cartridge.

    ...
    Attributes
    ----------
    TODO


    """
    # TODO implement rambanks
    def __init__(self, ramsize):
        """
        Ramsize is specified in cartridge at 0x149
        is 0,1,2,3.
        """
        self.vram = bytearray(0x2000)
        self.wram = bytearray(0x2000)
        if ramsize == 0:
            self.extram = None
        elif ramsize == 1:
            log.critical('rambank not implemented!')
            self.extram = bytearray(0x2000)
        elif ramsize == 2:
            log.critical('rambank not implemented!')
            self.extram = bytearray(0x8000)
        elif ramsize == 3:
            log.critical('rambank not implemented!')
            self.extram = bytearray(0x32000)
    
    def read_byte(self, address):
        """
        Read a byte from the rambanks.

        Parameters
        ----------
        address : int
            Address in range 0x8000-0xdfff
        Returns
        -------
        int
            byte read
        """
        if address < 0x8000:
            log.critical('Invalid read from ram bank!')
            return 0
        elif address < 0xa000:
            return self.vram[address - 0x8000]
        elif address < 0xc000:
            if self.extram == None:
                log.critical('Invalid read from nonexistant external ram!')
            else:
                return self.extram[address - 0xa000]
        elif address < 0xe000:
            return self.wram[address - 0xc000]

    def write_byte(self, byte, address):
        """
        write a byte at address.

        Parameters
        ----------
        byte : int
            to write
        address : int
            to write to in valid range 0x8000-0xdfff
        """
        if address < 0x8000:
            log.critical('invalid write to ram banks!')
        elif address < 0xa000:
            self.vram[address - 0x8000] = byte & 0xff
        elif address < 0xc000:
            log.critical('not implemented ram banking!')
        elif address < 0xe000:
            self.wram[address - 0xc000] = byte & 0xff

