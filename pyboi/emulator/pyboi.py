from ..processor.z80 import Z80
from ..memory.mem import Memory
from ..gpu.gpu import GPU
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..base import Base
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(name='pyboi')

class Pyboi:
    """
    A GB emulator class.

    Attributes
    ----------
    mem : Memory class
        internal memory of the GB
    z80 : Z80 class
        processor of the GB
    gpu : GPU class
        renders graphics
    engine : SQLAlchemy engine
        engine for saving the game states in SQLAlchemy's database

    """
    def __init__(self):
        self.mem = Memory()
        self.z80 = Z80(self.mem)
        self.gpu = GPU(self.mem)
        self.engine = create_engine('sqlite:///pyboi_saves.db')
        Base.metadata.create_all(self.engine)
    
    def save(self, save_name):
        """
        Save the current pyboi state.

        Parameters
        ----------
        save_name : string
            name to save the current state as

        """
        Session = sessionmaker(bind=self.engine)
        session = Session()
        self.z80.save_state(save_name, session)

    def load_rom(self, rom):
        """
        Load a rom into the GB.

        Parameters
        ----------
        rom : path (string)
            path to the rom file to load

        """
        self.mem.load_rom(rom)

    def boot(self):
        """
        Runs the bios and stops after completed.
        Requires a rom to be loaded.
        """
        self.mem.set_bios_mode(True)
        for _ in range(9000000):
            cycles = self.z80.execute_boot_opcode()
            #self.gpu.update_graphics(cycles)
        self.mem.set_bios_mode(False)

    def init_boot(self):
        """
        Sets up to run the bootstrap "bios".
        """
        self.z80.init_boot()

    def get_boot_frame(self):
        """
        Runs enough clock cycles to get one frame.
        ...
        Returns
        -------
        bytearray object representing the frame
        """
        self.mem.set_bios_mode(True)
        count = 0
        while count < 70224:
            cycles = self.z80.execute_boot_opcode()
            self.gpu.update_graphics(cycles)
            count += cycles
        return self.gpu.get_frame_buffer()
        self.mem.set_bios_mode(False)

    def get_frame(self):
        """
        Runs enough clock cycles to get one frame.
        ...
        Returns
        -------
        bytearray object representing the frame
        """
        count = 0
        while count < 70224:
            cycles = self.z80.execute_opcode()
            self.gpu.update_graphics(cycles)
            count += cycles
        return self.gpu.get_frame_buffer()

    def run(self):
        """ Start execution of the emulator. """
        for _ in range(95200828):
            cycles = self.z80.execute_opcode()
            self.gpu.update_graphics(cycles)


