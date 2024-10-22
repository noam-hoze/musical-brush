import pygame
import numpy as np
import os
from datetime import datetime
import wave

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

# New variables for recording
recording = False
recorded_sounds = []
current_recording = None

# Button dimensions and positions
button_width, button_height = 80, 30
button_margin = 10
record_button = pygame.Rect(width - 3 * (button_width + button_margin), 10, button_width, button_height)
stop_button = pygame.Rect(width - 2 * (button_width + button_margin), 10, button_width, button_height)
play_button = pygame.Rect(width - (button_width + button_margin), 10, button_width, button_height)

# Font for button text
font = pygame.font.Font(None, 24)

# Modified play_sound function
def play_sound(frequency):
    global recording, recorded_sounds
    duration = 200  # milliseconds
    sample_rate = 44100
    t = np.linspace(0, duration / 1000, int(duration * sample_rate / 1000), False)
    
    wave = np.sin(2 * np.pi * frequency * t)
    envelope = np.exp(-t * 5)  # Adjust the decay rate as needed
    sound = (wave * envelope * 32767).astype(np.int16)
    
    # Convert mono to stereo
    stereo_sound = np.column_stack((sound, sound))
    
    if recording:
        recorded_sounds.append(stereo_sound)
    
    sound = pygame.sndarray.make_sound(stereo_sound)
    sound.play()

# Function to save recording
def save_recording():
    global recorded_sounds
    if not os.path.exists("recordings"):
        os.makedirs("recordings")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recordings/recording_{timestamp}.wav"
    
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(2)  # Changed to 2 channels for stereo
        wf.setsampwidth(2)
        wf.setframerate(44100)
        for sound in recorded_sounds:
            wf.writeframes(sound.tobytes())
    
    recorded_sounds = []
    return filename

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
            x, y = event.pos
            if record_button.collidepoint(x, y):
                recording = True
                recorded_sounds = []
            elif stop_button.collidepoint(x, y):
                if recording:
                    recording = False
                    current_recording = save_recording()
            elif play_button.collidepoint(x, y):
                if current_recording:
                    pygame.mixer.music.load(current_recording)
                    pygame.mixer.music.play()
            else:
                dragging = True
                last_played_index = -1
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
    
    # Draw buttons
    pygame.draw.rect(screen, (255, 0, 0) if recording else (200, 200, 200), record_button)
    pygame.draw.rect(screen, (200, 200, 200), stop_button)
    pygame.draw.rect(screen, (200, 200, 200), play_button)
    
    # Add text to buttons
    screen.blit(font.render("Record", True, (0, 0, 0)), (record_button.x + 10, record_button.y + 5))
    screen.blit(font.render("Stop", True, (0, 0, 0)), (stop_button.x + 20, stop_button.y + 5))
    screen.blit(font.render("Play", True, (0, 0, 0)), (play_button.x + 20, play_button.y + 5))
    
    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()
