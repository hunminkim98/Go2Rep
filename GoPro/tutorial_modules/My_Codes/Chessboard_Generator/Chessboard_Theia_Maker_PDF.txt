import numpy as np
import matplotlib.pyplot as plt

def create_checkerboard_image(square_px=1000, rows=8, cols=5):
    board = np.zeros((rows * square_px, cols * square_px, 3), dtype=np.uint8)

    for i in range(rows):
        for j in range(cols):
            color = [255, 255, 255] if (i + j) % 2 == 0 else [0, 0, 0]
            board[i*square_px:(i+1)*square_px, j*square_px:(j+1)*square_px] = color

    # Set bottom-left two squares to blue
    board[6*square_px:7*square_px, 1*square_px:2*square_px] = [0, 0, 255]
    board[7*square_px:8*square_px, 0*square_px:1*square_px] = [0, 0, 255]

    return board

# === Desired physical dimensions ===
square_size_mm = 170
dpi = 254  # 254 DPI = 100 px/cm = ~1000 px per 100mm
rows, cols = 8, 5

# === Create checkerboard ===
square_px = int((square_size_mm / 25.4) * dpi)
img = create_checkerboard_image(square_px=square_px, rows=rows, cols=cols)

# === Total size in inches ===
width_in = (img.shape[1]) / dpi
height_in = (img.shape[0]) / dpi

# === Create figure and embed image directly ===
fig = plt.figure(figsize=(width_in, height_in), dpi=dpi)
fig.figimage(img, xo=0, yo=0)  # Position at bottom-left with no axes

# === Save without bounding box or padding ===
fig.savefig("checkerboard_170mm_squares_fixed.pdf", format='pdf', dpi=dpi)
plt.close()

print("✅ PDF saved with EXACT 100mm squares: checkerboard_100mm_squares_fixed.pdf")
