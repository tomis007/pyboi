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
        Human readable error message, or None on success
        """
        print(rom)
        print("loading rom")

    def load_save(self, save_name):
        print("loading save!")
    
