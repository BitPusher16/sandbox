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

    #filename = 'right_half_16x16.png'
    filename = 'box_16x16.png'
    with open(filename, "wb") as f:
        writer = png.Writer(width=width, height=height, greyscale=True)
        writer.write(f, png_data.tolist())

def png_to_numpy_zero_one(filepath):
    reader = png.Reader(filepath)
    width, height, rows, info = reader.asDirect()

    img_array = np.stack(list(rows))
    if info['bitdepth'] == 8:
        img_array = img_array / 255.0

    img_array = img_array.astype(int)
    return img_array

def tmp():
    print(png_to_numpy_zero_one('box_16x16.png'))

def pr(A):
    with np.printoptions(formatter={'float': '{:6.2f}'.format}):
        print(A)

def one_dim_advec():
    x = 1
    y = 2
    z = x + y
    print(z)

    #list_a = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    #arr = np.array([list_a], dtype=object)

    U = 1.0
    for U in (0.5, 1.0, 1.5):
        delta_x = 1.0
        m, n = 1, 10
        A = np.zeros((m, n))
        A[0,0] = 1

        pr(A)
        for t in range(12):
            cpy = A.copy()
            for (i, j), val in np.ndenumerate(A):
                q_curr = A[i,j]
                q_prev = A[i,(j-1) % A.shape[1]]
                del_q_del_x = (q_curr - q_prev) / delta_x

                #if t == 0 and i == 0 and j == 0:
                    #foo = 10 #dbg
                cpy[i,j] = A[i,j] - U * del_q_del_x
            A = cpy
            pr(A)
        print()

def main() -> None:
    print('hello')
    #create_simple_png()
    #tmp()
    one_dim_advec()

    print('goodbye')
