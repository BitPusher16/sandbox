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
import time

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

#def png_to_numpy_zero_one(filepath):
#    reader = png.Reader(filepath)
#    width, height, rows, info = reader.asDirect()
#
#    img_array = np.stack(list(rows))
#    if info['bitdepth'] == 8:
#        img_array = img_array / 255.0
#
#    img_array = img_array.astype(int)
#    return img_array

def png_to_numpy_zero_one(filepath):
    reader = png.Reader(filepath)
    width, height, rows, info = reader.asDirect()

    # 1. Stack the flat rows into a 2D numpy array
    img_array = np.stack(list(rows))
    
    # 2. Reshape from (height, width * planes) to (height, width, planes)
    planes = info['planes']  # 3 for RGB, 4 for RGBA
    img_array = img_array.reshape(height, width, planes)
    
    # 3. Scale 8-bit images to 0.0 - 1.0 range
    if info['bitdepth'] == 8:
        img_array = img_array / 255.0

    # 4. Extract color channels (ignore alpha channel if it exists)
    color_channels = img_array[:, :, :3]

    # 5. Create a 2D boolean mask
    # True if R, G, and B are all 0 (black). False otherwise.
    is_black = np.all(color_channels == 0.0, axis=-1)
        
    return is_black



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
    clear = True  # set False to scroll instead of redrawing in place
    lines = []
    for row in np.atleast_2d(np.asarray(A, dtype=float)):
        #lines.append("".join(f"{_bg(x)}{x:4.1f}{RESET}" for x in row))
        #lines.append("".join(f"{_bg(x)}{x:2.0f}{RESET}" for x in row))
        lines.append("".join(f"{_bg(x)}  {RESET}" for x in row))
    lines.append("") # empty line at end.
    frame = "\n".join(lines)

    # back buffer: assemble off-screen, then present atomically
    parts = ["\033[?2026h", "\033[?25l"]  # begin synced update, hide cursor
    if clear:
        parts.append("\033[H")            # home; do not 2J (that flashes)
    parts.append(frame)
    parts.append("\033[J")                # erase leftover rows below the frame
    parts.append("\033[?2026l")           # end synced update = toggle/present
    print("".join(parts), end="", flush=True)

def arry_normalize(a):
    return (a - np.min(a)) / (np.max(a) - np.min(a))

def masked_normalize(a, mask):
    masked_data = np.ma.masked_array(a, mask=mask)
    data_min = masked_data.min()
    data_max = masked_data.max()
    normalized_masked = (masked_data - data_min) / (data_max - data_min)
    return normalized_masked


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
                    #foo = 10
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
                q_curr = A[i,j]
                q_prev = A[i,(j-1) % A.shape[1]]
                q_next = A[i,(j+1) % A.shape[1]]
                part2_q_part_x2 = (q_next - 2*q_curr + q_prev) / delta_x ** 2

                #if t == 0 and i == 0 and j == 3:
                    #foo = 10

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

    #U = 1.0  # horizontal velocity
    #V = 0.6  # vertial velocity
    nu = 1.0 # diffusion rate.
    delta_x = 1.0
    delta_y = 1.0


    #for delta_t in (0.2,): # checkerboard
    for delta_t in (0.1,): # checkerboard

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

        wall = np.zeros((m,n), dtype=bool)
        wall[4,6] = True
        wall[4,7] = True
        wall[4,8] = True
        wall[5,6] = True
        wall[5,7] = True
        wall[5,8] = True
        wall[6,6] = True
        wall[6,7] = True
        wall[6,8] = True

        U = np.zeros((m,n))
        V = np.zeros((m,n))
        u_default = 1.0
        v_default = 0.6

        for (i, j), val in np.ndenumerate(A):
            if not wall[i,j]:
                U[i,j] = u_default
                V[i,j] = v_default

        C_i_C_j = (u_default + v_default) * delta_t / delta_x    # should be <= 1.
        r = nu * delta_t / delta_x**2            # should be <= 1/4 for 2d.
        foo = C_i_C_j + 4*r
        print(C_i_C_j, r, foo)

        t = 0
        pr(A)
        print()
        for step in range(20):
            cpy = A.copy()
            for (i, j), val in np.ndenumerate(A):
                if wall[i,j]:
                    continue
                q_cr = A[i,j]
                q_lt = 0 if wall[i,(j-1) % A.shape[1]] else A[i,(j-1) % A.shape[1]]
                q_rt = 0 if wall[i,(j+1) % A.shape[1]] else A[i,(j+1) % A.shape[1]]
                q_up = 0 if wall[(i-1) % A.shape[0],j] else A[(i-1) % A.shape[0], j]
                q_dn = 0 if wall[(i+1) % A.shape[0],j] else A[(i+1) % A.shape[0], j]

                laplace_q = (q_rt + q_lt + q_dn + q_up - 4*q_cr) / (delta_x**2)

                cpy[i,j] = q_cr \
                    - U[i,j] * delta_t * ((q_cr - q_lt) / delta_x) \
                    - V[i,j] * delta_t * ((q_cr - q_up) / delta_x) \
                    + nu * delta_t * laplace_q
            A = cpy
            pr(A)
            print()

def lbm_simple_f():
    m, n, p = 5, 5, 9
    f = np.zeros((m, n, p))
    f[2, 3, 1] = 1

    pr(f[:,:,1])
    print()

    hop_offsets = list()
    hop_offsets.append([ 0, 0])
    hop_offsets.append([ 0, 1])
    hop_offsets.append([-1, 0])
    hop_offsets.append([ 0,-1])
    hop_offsets.append([ 1, 0])
    hop_offsets.append([-1, 1])
    hop_offsets.append([-1,-1])
    hop_offsets.append([ 1,-1])
    hop_offsets.append([ 1, 1])
    
    f_new = np.zeros((m, n, p))

    for (i, j, k), val in np.ndenumerate(f):
        i_wrapped = (i - hop_offsets[k][0]) % f.shape[0]
        j_wrapped = (j - hop_offsets[k][1]) % f.shape[1]
        f_new[i,j,k] = f[i_wrapped, j_wrapped, k]
        pass
    
    f = f_new
    pr(f[:,:,1])

def collide():
    m, n, p = 1, 1, 9
    f = np.zeros((m, n, p))
    #f[0,0,1] = 0.1
    f[0,0,:] = [4/9, 1/9, 1/9, 1/9, 1/9, 1/36, 1/36, 1/36, 1/36]

    delta_j = [0, 1, 0, -1, 0, 1, -1, -1, 1]
    delta_i = [0, 0, -1, 0, 1, -1, -1, 1, 1]
    w = [4/9, 1/9, 1/9, 1/9, 1/9, 1/36, 1/36, 1/36, 1/36]

    rho = 0
    for k in range(9):
        rho += f[0,0,k]
    u = 0
    v = 0
    for k in range(9):
        u += f[0,0,k] * delta_j[k]
        v += f[0,0,k] * delta_i[k]
    u /= rho
    v /= rho

    print(rho, u, v)

    f_eq = np.zeros((m, n, p))
    speed2 = u*u + v*v

    for k in range(9):
        s = delta_j[k] * u + delta_i[k] * v
        f_eq[0,0,k] = w[k] * rho * (1 + 3*s + 4.5 * s * s - 1.5 * speed2)

    print(f_eq[0,0,:])

    tau = 1
    for k in range(9):
        f[0,0,k] = f[0,0,k] - (1/tau) * (f[0,0,k] - f_eq[0,0,k])

    print(f_eq[0,0,:])

def collide_small_grid():

    delta_j = [0, 1, 0, -1, 0, 1, -1, -1, 1]
    delta_i = [0, 0, -1, 0, 1, -1, -1, 1, 1]
    w = [4/9, 1/9, 1/9, 1/9, 1/9, 1/36, 1/36, 1/36, 1/36]
    tau = 1
    opp = [0, 3, 4, 1, 2, 7, 8, 5, 6]

    # inlet.
    rho_in = 1
    u_in = 0.05
    v_in = 0

    m, n, p = 5, 5, 9
    #m, n, p = 12, 12, 9
    f = np.zeros((m, n, p))
    wall = np.zeros((m,n), dtype=bool)

    # initialize f to rest weights
    for (i, j, k), val in np.ndenumerate(f):
        f[i,j,k] = w[k]

    # small disturbance.
    #f[2,1,1] += 0.25

    # set up wall.
    #wall[:,4] = True
    #f[:,4,:] = 0 # walls have no fluid.
    wall[2,4] = True
    wall[3,4] = True
    for i in range(m):
        for j in range(n):
            for k in range(p):
                if wall[i,j]:
                    f[i,j,k] = 0

    for step in range(8):

        # collide.

        #f_collided = f.copy()
        f_collided = np.zeros((m, n, p))
        f_eq = np.zeros((m, n, p))
        for i in range(m):
            for j in range(n):
                if wall[i,j]:
                    continue

                rho = 0
                for k in range(p):
                    rho += f[i,j,k]

                u = 0
                v = 0
                for k in range(p):
                    u += (f[i,j,k] * delta_j[k])
                    v += (f[i,j,k] * delta_i[k])
                u /= rho
                v /= rho

                #f_eq = np.zeros((m, n, p))
                speed2 = u*u + v*v

                # f_eq for this cell.
                for k in range(p):
                    s = delta_j[k] * u + delta_i[k] * v
                    f_eq[i,j,k] = w[k] * rho * (1 + 3*s + 4.5 * s * s - 1.5 * speed2)

                for k in range(p):
                    f_collided[i,j,k] = f[i,j,k] - (1/tau) * (f[i,j,k] - f_eq[i,j,k])

        #stream.

        f_stream = f.copy()
        for i in range(m):
            for j in range(n):
                if wall[i,j]:
                    continue

                for k in range(p):
                    i_wrapped = (i-delta_i[k]) % f.shape[0]
                    j_wrapped = (j-delta_j[k]) % f.shape[1]

                    if wall[i_wrapped,j_wrapped]:
                        # donor cell is a wall.
                        f_stream[i,j,k] = f_collided[i, j, opp[k]]
                    else:
                        # donor cell is not a wall.
                        f_stream[i,j,k] = f_collided[i_wrapped, j_wrapped, k]

        # overwrite stream at inlet.
        for i in range(m):
            for j in range(1):
                if wall[i,j]:
                    continue
                for k in range(p):
                    s = delta_j[k] * u_in + delta_i[k] * v_in
                    f_stream[i, j, k] = w[k] * rho_in * (1+3*s + 4.5*s*s - 1.5*(u_in**2))
                
        f = f_stream

        f_sum = np.sum(f, axis=2)
        print('f_sum:')
        print(f_sum)
        print()

        # debug. i did not store u in a grid, so need to compute that now.
        u_grid = np.zeros((m, n, p))
        for i in range(m):
            for j in range(n):
                if wall[i,j]:
                    continue
                rho = 0
                for k in range(p):
                    rho += f[i,j,k]
                u = 0
                v = 0
                for k in range(p):
                    u += (f[i,j,k] * delta_j[k])
                    v += (f[i,j,k] * delta_i[k])
                u /= rho
                v /= rho

                u_grid[i,j] = u

        u_sum = np.sum(u_grid, axis=2)
        print('u_sum:')
        print(u_sum)
        print()

        #pr(arry_normalize(f_sum))
        #print()
        #time.sleep(0.1)

def lattice_units():
    mach_lattice_cells_per_second = 1 / math.sqrt(3)
    mach_lattice_squared = mach_lattice_cells_per_second**2

    nu_physical_m2_per_sec = 1.5 * 10**-5
    obstacle_width_pixels = 40
    png_width_physical_m = 2
    png_width_pixels = 400
    pixel_width_m = png_width_physical_m / png_width_pixels # 0.005
    delta_x_physical_m = pixel_width_m
    delta_y_physical_m = pixel_width_m

    u_physical_m_per_sec = 10
    #u_pixels_per_sec = u_physical_m_per_sec * pixel_width_m # this should be chosen, not computed.
    u_cells_per_step = 0.05

    delta_t_seconds = delta_x_physical_m * (u_cells_per_step / u_physical_m_per_sec)
    tau = (1/2) + (3*nu_physical_m2_per_sec * u_cells_per_step)/(u_physical_m_per_sec*delta_x_physical_m)

    nu_lattice_px2_per_step = nu_physical_m2_per_sec * (1/pixel_width_m)**2 * delta_t_seconds

    re = u_cells_per_step * obstacle_width_pixels / nu_lattice_px2_per_step

    print(delta_t_seconds)
    print(tau)
    print(nu_lattice_px2_per_step)
    print(re)

def operable_case():
    u_lat = 0.05
    L_lat = 20 # pixels
    re = 100
    nu_lat = u_lat * L_lat / re
    tau = (1/2) + 3*nu_lat

    print(nu_lat)
    print(tau)


def operable_run():
    arry = png_to_numpy_zero_one('shapes/naca2412_5deg_20pct_32h_64w.png')

    delta_j = [0, 1, 0, -1, 0, 1, -1, -1, 1]
    delta_i = [0, 0, -1, 0, 1, -1, -1, 1, 1]
    w = [4/9, 1/9, 1/9, 1/9, 1/9, 1/36, 1/36, 1/36, 1/36]
    tau = 0.6
    opp = [0, 3, 4, 1, 2, 7, 8, 5, 6]

    # inlet.
    rho_in = 1
    u_in = 0.05
    v_in = 0

    #m, n, p = 12, 24, 9
    m, n, p = arry.shape[0], arry.shape[1], 9
    f = np.zeros((m, n, p))
    u = np.zeros((m, n))
    v = np.zeros((m, n))
    #wall = np.zeros((m,n), dtype=bool)
    wall = arry.copy()

    # initialize f to rest weights
    for (i, j, k), val in np.ndenumerate(f):
        f[i,j,k] = w[k]

    # set up wall.
    #wall[5:7,4:10] = True
    for i in range(m):
        for j in range(n):
            for k in range(p):
                if wall[i,j]:
                    f[i,j,k] = 0

    dPx_cumulative = 0
    dPy_cumulative = 0
    steps = 4000
    skip_steps = math.floor(2 * n / u_in)

    #for step in range(4000):
    #for step in range(2):
    for step in range(steps):

        # track lift, drag for this step.
        dPx = 0
        dPy = 0

        # collide.

        f_eq = np.zeros((m, n, p))
        f_collided = np.zeros((m, n, p))

        for i in range(m):
            for j in range(n):
                if wall[i,j]:
                    continue

                rho = 0
                for k in range(p):
                    rho += f[i,j,k]

                u[i,j] = 0
                v[i,j] = 0
                for k in range(p):
                    u[i,j] += (f[i,j,k] * delta_j[k])
                    v[i,j] += (f[i,j,k] * delta_i[k])
                u[i,j] /= rho
                v[i,j] /= rho

                speed2 = u[i,j]*u[i,j] + v[i,j]*v[i,j]

                # f_eq for this cell.
                for k in range(p):
                    s = delta_j[k] * u[i,j] + delta_i[k] * v[i,j]
                    f_eq[i,j,k] = w[k] * rho * (1 + 3*s + 4.5 * s * s - 1.5 * speed2)

                for k in range(p):
                    f_collided[i,j,k] = f[i,j,k] - (1/tau) * (f[i,j,k] - f_eq[i,j,k])

        #stream.

        f_stream = f.copy()
        for i in range(m):
            for j in range(n):
                if wall[i,j]:
                    continue

                for k in range(p):
                    i_wrapped = (i-delta_i[k]) % f.shape[0]
                    j_wrapped = (j-delta_j[k]) % f.shape[1]

                    if wall[i_wrapped,j_wrapped]:
                        # donor cell is a wall.
                        f_stream[i,j,k] = f_collided[i, j, opp[k]]

                        # here is a fine place to record momentum.
                        # note: because we use -2, this shows force exerted on the body,
                        # not the fluid.
                        dPx += -2 * f_collided[i, j, opp[k]] * delta_j[k]
                        dPy += -2 * f_collided[i, j, opp[k]] * delta_i[k]
                    else:
                        # donor cell is not a wall.
                        f_stream[i,j,k] = f_collided[i_wrapped, j_wrapped, k]

        # overwrite stream at inlet.
        for i in range(m):
            for j in range(1):
                if wall[i,j]:
                    continue
                for k in range(p):
                    s = delta_j[k] * u_in + delta_i[k] * v_in
                    f_stream[i, j, k] = w[k] * rho_in * (1+3*s + 4.5*s*s - 1.5*(u_in**2))

        # overwrite at outlet.
        #f_stream[:, -1, :] = f_stream[:, 0, :]
        f_stream[:, -1, :] = f_stream [:, -2, :]
                
        # next f is computed. replace f with it.
        f = f_stream

        if step - skip_steps >= 0:
            dPx_cumulative += dPx
            dPy_cumulative += dPy

        if step % 50 == 0:
            #print(f'dPx:{dPx: 10.8f}  dPy:{dPy: 10.8f}')

            f_sum = np.sum(f, axis=2)
            max_u = np.max(u)

            #print('f_sum:')
            #print(f_sum)
            #print('max_u:')
            #print(max_u)
            #pr(arry_normalize(f_sum))
            #pr(masked_normalize(f_sum, wall))
            #print()

        pr(masked_normalize(np.sum(f, axis=2), wall))

    #pr(masked_normalize(np.sum(f, axis=2), wall))
    #print()
    #pr(masked_normalize(np.sqrt(u**2 + v**2), wall))
    #print()
    #print()
    #max_u = np.max(u)
    #print(f'max_u: {max_u}')

    print(f'steps:{steps}, skip_steps:{skip_steps}')
    print(f'avg dPx: {dPx_cumulative / (steps - skip_steps)}')
    print(f'avg dPy: {dPy_cumulative / (steps - skip_steps)}')



def main() -> None:
    print('hello')
    #create_simple_png()
    #tmp()
    #one_dim_advec()
    #one_dim_diffusion()
    #one_dim_diffus_advec()
    #two_dim_diffus_advec()
    #lbm_simple_f()
    #collide()
    #collide_small_grid()
    #lattice_units()
    #operable_case()
    operable_run()

    print('goodbye')




























