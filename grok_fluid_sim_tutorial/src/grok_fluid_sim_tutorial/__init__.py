# pyright: reportUnusedVariable = false
# pyright: reportMissingTypeStubs = false
# pyright: reportUnannotatedClassAttribute = false
# pyright: reportImplicitOverride = false
# pyright: reportUnusedCallResult = false
# pyright: reportUnknownMemberType = false
# pyright: reportUnknownArgumentType = false
# pyright: reportUnknownParameterType = false
# pyright: reportUnknownVariableType = false
# pyright: reportMissingParameterType = false
# pyright: reportAny = false
# pyright: reportConstantRedefinition = false

import numpy as np
import png
import math

class Point:
    """A class representing a 2D point on a Cartesian plane."""
    
    def __init__(self, x: float = 0.0, y: float = 0.0):
        # Members (attributes)
        self.x = x
        self.y = y
        
    def distance_from_origin(self) -> float:
        """Calculates the distance from (0, 0)."""
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def distance_to(self, other: "Point") -> float:
        """Calculates the distance to another Point object."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def move(self, dx: float, dy: float):
        """Shifts the point by dx and dy amounts."""
        self.x += dx
        self.y += dy
        
    def __str__(self) -> str:
        """Returns a user-friendly string representation."""
        return f"({self.x}, {self.y})"

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

#def pr(A):
#    with np.printoptions(formatter={'float': '{:6.2f}'.format}):
#        print(A)

RESET = "\033[0m"

def _bg(v):
    v = 0.0 if v < 0 else 1.0 if v > 1 else float(v)
    n = 232 + int(round(v * 23))
    return f"\033[48;5;{n}m"

def pr(A):
    for row in np.atleast_2d(np.asarray(A, dtype=float)):
        print("".join(f"{_bg(x)}{x:6.2f}{RESET}" for x in row))

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
                part_q_part_x = (q_curr - q_prev) / delta_x

                #if t == 0 and i == 0 and j == 0:
                    #foo = 10 #dbg
                cpy[i,j] = A[i,j] - U * part_q_part_x
            A = cpy
            pr(A)
        print()

def one_dim_diffusion():
    m, n = 1, 10

    nu = 1
    delta_x = 1
    for r in (0.25, 0.5, 0.6):
        A = np.zeros((m,n))
        A[0,3] = 0.5
        A[0,4] = 1
        A[0,5] = 0.5

        delta_t = r * delta_x * delta_x / nu
        t = 0
        for step in range(20):
            cpy = A.copy()
            for (i, j), val in np.ndenumerate(A):
                q_curr = A[i,j] #dbg
                q_prev = A[i,(j-1) % A.shape[1]]
                q_next = A[i,(j+1) % A.shape[1]]
                part2_q_part_x2 = (q_next - 2*q_curr + q_prev) / delta_x ** 2

                #if t == 0 and i == 0 and j == 3:
                    #foo = 10 #dbg

                cpy[i,j] = A[i,j] + nu * delta_t * part2_q_part_x2
            A = cpy
            pr(A)

def one_dim_diffus_advec():
    m, n = 1, 16

    #C = 0.8  # Courant Number
    #r = 0.4
    U = 1.0  # conveyor velocity
    nu = 1.0 # diffusion rate.
    delta_x = 1.0
    delta_t = 0.25

    for delta_t in (0.25, 0.6, 1.2):

        # from Courant Number and r, we can determine delta_t.
        #delta_t_C = C * delta_x / U
        #delta_t_r = r * delta_x**2 / nu
        #delta_t = min(delta_t_C, delta_t_r)
        #print(delta_t_C, delta_t_r, delta_t)
        # update: actually we should be computing Courant Number and r from delta_t.

        C = U * delta_t / delta_x      # should be <= 1
        r = nu * delta_t / delta_x**2  # should be <= 1/2.
        print(C, r)

        A = np.zeros((m,n))
        A[0,3] = 0.5
        A[0,4] = 1
        A[0,5] = 0.5

        t = 0
        pr(A)
        for step in range(16):
            cpy = A.copy()
            for (i, j), val in np.ndenumerate(A):
                q_curr = A[i,j]
                q_prev = A[i,(j-1) % A.shape[1]]
                q_next = A[i,(j+1) % A.shape[1]]

                part2_q_part_x2 = (q_next - 2*q_curr + q_prev) / delta_x ** 2
                part_q_part_x = (q_curr - q_prev) / delta_x

                #if t == 0 and i == 0 and j == 3:
                    #foo = 10 #dbg

                cpy[i,j] = A[i,j] \
                    + (nu * delta_t * part2_q_part_x2) \
                    - (U * delta_t * part_q_part_x)
            A = cpy
            pr(A)

def two_dim_diffus_advec():
    m, n = 12, 12

    U = 1.0  # horizontal velocity
    V = 0.6  # vertial velocity
    nu = 1.0 # diffusion rate.
    delta_x = 1.0
    delta_y = 1.0


    #for delta_t in (0.2,): # checkerboard
    for delta_t in (0.1,): # checkerboard

        C_i_C_j = (U + V) * delta_t / delta_x    # should be <= 1.
        r = nu * delta_t / delta_x**2            # should be <= 1/4 for 2d.
        foo = C_i_C_j + 4*r
        print(C_i_C_j, r, foo)

        A = np.zeros((m,n))
        A[1,1] = 1
        A[1,2] = 1
        A[1,3] = 1
        A[2,1] = 1
        A[2,2] = 1
        A[2,3] = 1
        A[3,1] = 1
        A[3,2] = 1
        A[3,3] = 1

        t = 0
        pr(A)
        print()
        for step in range(20):
            cpy = A.copy()
            for (i, j), val in np.ndenumerate(A):
                q_cr = A[i,j]
                q_lt = A[i,(j-1) % A.shape[1]]
                q_rt = A[i,(j+1) % A.shape[1]]
                q_up = A[(i-1) % A.shape[0], j]
                q_dn = A[(i+1) % A.shape[0], j]

                laplace_q = (q_rt + q_lt + q_dn + q_up - 4*q_cr) / (delta_x**2)

                cpy[i,j] = q_cr \
                    - U * delta_t * ((q_cr - q_lt) / delta_x) \
                    - V * delta_t * ((q_cr - q_up) / delta_x) \
                    + nu * delta_t * laplace_q
            A = cpy
            pr(A)
            print()

def main() -> None:
    print('hello')
    #create_simple_png()
    #tmp()
    #one_dim_advec()
    #one_dim_diffusion()
    #one_dim_diffus_advec()
    two_dim_diffus_advec()

    print('goodbye')
