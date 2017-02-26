#! /usr/bin/env python3
import logging
from pyboi import Pyboi

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(name='run')

# just basic functionality testing
def main():
    log.debug('creating a pyboi class instance')
    gameboy = Pyboi()
    log.debug('loading file "tetris.gb"')
    gameboy.load_rom('tetris.gb')
    log.debug('attempting to save the game to "mysave1"')
    gameboy.save('mysave1')


if __name__ == "__main__":
    main()
