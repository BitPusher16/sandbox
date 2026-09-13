import numpy as np
import png

def create_simple_png():

    height = 16
    width = 16

    grid = np.zeros((height, width), dtype=np.uint8)
    #grid[:,width // 2 :] = 1 # set right half to 1
    grid[:,:] = 1
    grid[1:-1,1:-1] = 0


    png_data = grid * 255

    #filename = "right_half_16x16.png"
    filename = "box_16x16.png"
    with open(filename, "wb") as f:
        writer = png.Writer(width=width, height=height, greyscale=True)
        writer.write(f, png_data.tolist())

def main() -> None:
    print('hello')
    create_simple_png()
    print('goodbye')
