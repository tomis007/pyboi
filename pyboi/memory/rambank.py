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
    def __init__(self, ramsize):
        """
        Ramsize is specified in cartridge at 0x149
        is 0,1,2,3.
        """
        self.vram = bytearray(0x2000)
        self.wram = bytearray(0x2000)
        self.extram_enabled = True
        self.bank_size = 0
        self.ram_offset = 0
        if ramsize == 0:
            self.extram = None
        elif ramsize == 1:
            self.extram = bytearray(0x800)
        elif ramsize == 2:
            self.extram = bytearray(0x2000)
        elif ramsize == 3:
            self.extram = bytearray(0x8000)
            self.bank_size = 0x2000
    
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
            log.error('Invalid read from ram bank!')
            return 0
        elif address < 0xa000:
            return self.vram[address - 0x8000]
        elif address < 0xc000:
            if self.extram == None:
                log.critical('Invalid read from nonexistant external ram!')
                quit()
            elif self.extram_enabled:
                return self.extram[(address - 0xa000) + self.ram_offset]
            else:
                log.error('EXTRAM DISABLED')
                return 0
        elif address < 0xe000:
            return self.wram[address - 0xc000]
        else:
            log.error('Invalid read from ram')
            return 0

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
            if self.extram_enabled and self.extram is not None:
                self.extram[(address - 0xa000) + self.ram_offset] = byte & 0xff
        elif address < 0xe000:
            self.wram[address - 0xc000] = byte & 0xff
        else:
            log.error('invalid write to ram')

    def set_ext_ram_enable(self, is_enabled):
        """
        Enables/Disables access to External ram
        """
        if is_enabled:
            log.debug('RAM ENABLED')
        else:
            log.debug('RAM DISABLED')
        self.extram_enabled = is_enabled


    def set_bank_num(self, num):
        """
        Changes the current RAM Bank selected.
        Only used with 4 blocks of 8kb ram. 
        num : 0-3
        """
        self.ram_offset = num * self.bank_size

