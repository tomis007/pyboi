#! /usr/bin/env python3

from pyboi import Pyboi
import drawille


def main():
    gb = Pyboi()
    gb.load_rom('roms/tetris.gb')
    c = drawille.Canvas()
    while True:
        c.clear()
        c.set(0,0)
        c.set(159, 143)
        frame = gb.get_boot_frame()
        for row in range(144):
            for col in range(160):
                if frame[(row * 160) + col] != 0:
                    c.set(col, row)
        print(chr(27) + "[2J")
        print(chr(27) + "[3J")
        print(c.frame())

if __name__ == "__main__":
    main()

