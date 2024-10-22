import pygame
import numpy as np

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Set up the display
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Pixel Sound App - C Lydian Scale (3 Octaves)")

# C Lydian scale frequencies (C3 to C6, 3 octaves)
c_lydian_frequencies = [
    130.81, 146.83, 164.81, 174.61, 196.00, 220.00, 246.94,  # C3 to B3
    261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88,  # C4 to B4
    523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77,  # C5 to B5
    1046.50  # C6
]

# Create a numpy array to store sound frequencies for each pixel
frequencies = np.zeros((height, width))
for y in range(height):
    for x in range(width):
        index = int(len(c_lydian_frequencies) * x / width)
        frequencies[y][x] = c_lydian_frequencies[index]

# Function to play harp-like sound based on pixel position
def play_sound(x, y):
    frequency = frequencies[y][x]
    duration = 500  # milliseconds
    sample_rate = 44100
    t = np.linspace(0, duration / 1000, int(duration * sample_rate / 1000), False)
    
    # Create a harp-like timbre using multiple harmonics
    wave = (
        np.sin(2 * np.pi * frequency * t) +
        0.5 * np.sin(4 * np.pi * frequency * t) +
        0.3 * np.sin(6 * np.pi * frequency * t) +
        0.2 * np.sin(8 * np.pi * frequency * t)
    )
    
    # Apply an envelope for a plucked string effect
    envelope = np.exp(-t * 8)
    wave = wave * envelope
    
    # Normalize and convert to 16-bit integer
    wave = wave / np.max(np.abs(wave))
    sound = np.asarray([32767 * wave, 32767 * wave]).T.astype(np.int16)
    sound = pygame.sndarray.make_sound(sound.copy())
    sound.play()

# Main game loop
running = True
dragging = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = False
        elif event.type == pygame.MOUSEMOTION and dragging:
            x, y = event.pos
            play_sound(x, y)
    
    # Clear the screen
    screen.fill((255, 255, 255))
    
    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()
