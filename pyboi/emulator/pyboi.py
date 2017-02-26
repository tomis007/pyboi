from ..processor.z80 import Z80
from ..memory.mem import Memory
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
    engine : SQLAlchemy engine
        engine for saving the game states in SQLAlchemy's database

    """
    def __init__(self):
        self.mem = Memory()
        self.z80 = Z80()
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
        for x in range(0x104, 0x134):
            print(hex(self.mem.read(x)))

