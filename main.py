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

# New variables for continuous harp phrase
last_played_index = -1
phrase_direction = 0  # 0 for no movement, 1 for up, -1 for down
phrase_speed = 0.1  # Adjust this to change the speed of the phrase

# Modified play_sound function
def play_sound(frequency):
    duration = 200  # milliseconds (shorter duration for quicker response)
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

# New function to play the harp phrase
def play_harp_phrase(x, y):
    global last_played_index, phrase_direction
    
    current_index = int(len(c_lydian_frequencies) * x / width)
    
    if last_played_index == -1:
        last_played_index = current_index
    elif current_index > last_played_index:
        phrase_direction = 1
    elif current_index < last_played_index:
        phrase_direction = -1
    else:
        phrase_direction = 0
    
    if phrase_direction != 0:
        last_played_index += phrase_direction
        last_played_index = max(0, min(last_played_index, len(c_lydian_frequencies) - 1))
        play_sound(c_lydian_frequencies[last_played_index])

# Main game loop
running = True
dragging = False
last_phrase_time = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            dragging = True
            last_played_index = -1  # Reset the phrase when starting a new drag
        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = False
        elif event.type == pygame.MOUSEMOTION and dragging:
            x, y = event.pos
            current_time = pygame.time.get_ticks()
            if current_time - last_phrase_time > phrase_speed * 1000:
                play_harp_phrase(x, y)
                last_phrase_time = current_time
    
    # Clear the screen
    screen.fill((255, 255, 255))
    
    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()
