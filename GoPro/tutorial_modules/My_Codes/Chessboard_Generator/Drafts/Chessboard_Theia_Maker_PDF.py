import numpy as np
import matplotlib.pyplot as plt

def create_checkerboard(rows=8, cols=5):
    board = np.zeros((rows, cols, 3), dtype=np.uint8)
    
    # Set black and white squares
    for i in range(rows):
        for j in range(cols):
            if (i + j) % 2 == 0:
                board[i, j] = [255, 255, 255]  # White
            else:
                board[i, j] = [0, 0, 0]  # Black
    
    # Set the top-left two squares to blue
    board[6, 1] = [0, 0, 255]  # Blue
    board[7, 0] = [0, 0, 255]  # Blue
    
    return board

# Create the checkerboard pattern
checkerboard = create_checkerboard()

# Display the checkerboard
plt.imshow(checkerboard)
plt.axis('off')  # Hide axes
plt.show()
