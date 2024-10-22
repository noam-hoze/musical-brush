import sys
print(sys.executable)
print(sys.path)

import pygame
import numpy as np
import os
from datetime import datetime
import wave
import time
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Suno API setup
SUNO_API_KEY = os.getenv('SUNO_API_KEY')
SUNO_API_URL = "https://api.suno.ai/v1/generate"

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
recorded_times = []
start_time = 0
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
    global recording, recorded_sounds, recorded_times, start_time
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
        recorded_times.append(time.time() - start_time)
    
    sound = pygame.sndarray.make_sound(stereo_sound)
    sound.play()

# Function to save recording
def save_recording():
    global recorded_sounds, recorded_times
    if not recorded_sounds:
        print("No sounds were recorded.")
        return None

    if not os.path.exists("recordings"):
        os.makedirs("recordings")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recordings/recording_{timestamp}.wav"
    
    # Calculate total duration
    total_duration = recorded_times[-1] + (recorded_sounds[-1].shape[0] / 44100)
    
    # Create output array (using float32 for intermediate calculations)
    total_samples = int(total_duration * 44100)
    output = np.zeros((total_samples, 2), dtype=np.float32)
    
    # Place sounds in the output array
    for sound, start_time in zip(recorded_sounds, recorded_times):
        start_sample = int(start_time * 44100)
        end_sample = start_sample + sound.shape[0]
        output[start_sample:end_sample] += sound.astype(np.float32) / 32767.0  # Normalize to [-1, 1] range
    
    # Normalize the output to prevent clipping
    max_amplitude = np.max(np.abs(output))
    if max_amplitude > 1.0:
        output /= max_amplitude
    
    # Convert back to int16
    output = (output * 32767).astype(np.int16)
    
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(output.tobytes())
    
    recorded_sounds = []
    recorded_times = []
    return filename

# New function to generate music using Suno API
def generate_music_from_recording(recording_file):
    with open(recording_file, 'rb') as file:
        headers = {
            "Cookie": "_ga=GA1.1.679676365.1727729613; ajs_anonymous_id=21e9d70b-1388-4b01-ac28-42d735bf3b85; __client_uat=1727729715; __client_uat_U9tcbTPE=1727729715; __refresh_U9tcbTPE=xIY168pZE9u2JqHgwmnY; _ga_7B0KEDD7XP=GS1.1.1729634259.5.1.1729634897.0.0.0; __session_U9tcbTPE=eyJhbGciOiJSUzI1NiIsImNhdCI6ImNsX0I3ZDRQRDExMUFBQSIsImtpZCI6Imluc18yT1o2eU1EZzhscWRKRWloMXJvemY4T3ptZG4iLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJzdW5vLWFwaSIsImF6cCI6Imh0dHBzOi8vc3Vuby5jb20iLCJleHAiOjE3Mjk2MzQ5NTcsImh0dHBzOi8vc3Vuby5haS9jbGFpbXMvY2xlcmtfaWQiOiJ1c2VyXzJlbTZBRXhLa0FOZzRJSjJUTTJQaTAzY3VLSyIsImh0dHBzOi8vc3Vuby5haS9jbGFpbXMvZW1haWwiOiJub2FtLmhvemVAZ21haWwuY29tIiwiaHR0cHM6Ly9zdW5vLmFpL2NsYWltcy9waG9uZSI6bnVsbCwiaWF0IjoxNzI5NjM0ODk3LCJpc3MiOiJodHRwczovL2NsZXJrLnN1bm8uY29tIiwianRpIjoiNjVmMzE1MThhMmYxYTFlYzA5YjkiLCJuYmYiOjE3Mjk2MzQ4ODcsInNpZCI6InNlc3NfMm1vNGhnVXF0Um94ck5lZXNFb1JEbmxrVjVtIiwic3ViIjoidXNlcl8yZW02QUV4S2tBTmc0SUoyVE0yUGkwM2N1S0sifQ.QaGRdyx7Im2KZUczjP7Rzb7ssJ9xwiqVJmSXplWKr4g_Hb62EimdzaZwfGtogTwMWY4VM7MEeSbN3gLxt5oS_WZ7YRCFjJManMQ78sySQiHAd9SXUVxGagVv_EwAs71Y04mH2GqZ69xPZGRl41mWfaTAkGe-pG3zektVn-0XyWI2KudAFsk0i9D1kxsGUFPPTwZ2RO8Vif_TzF-7jZEGgigVM2B_FnpezOOvAX3R9beqAJyvb0vjt5VT6a3rYRIQ4xrKC3K7uL9mqZJ6anYH8gk2Pb0CqFLU4CdLcqlwmeIMdlnCVhKGf5cpSLRsBx1NHtU64irl5FBCjfQNnZwnCg; __session=eyJhbGciOiJSUzI1NiIsImNhdCI6ImNsX0I3ZDRQRDExMUFBQSIsImtpZCI6Imluc18yT1o2eU1EZzhscWRKRWloMXJvemY4T3ptZG4iLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJzdW5vLWFwaSIsImF6cCI6Imh0dHBzOi8vc3Vuby5jb20iLCJleHAiOjE3Mjk2MzQ5NTcsImh0dHBzOi8vc3Vuby5haS9jbGFpbXMvY2xlcmtfaWQiOiJ1c2VyXzJlbTZBRXhLa0FOZzRJSjJUTTJQaTAzY3VLSyIsImh0dHBzOi8vc3Vuby5haS9jbGFpbXMvZW1haWwiOiJub2FtLmhvemVAZ21haWwuY29tIiwiaHR0cHM6Ly9zdW5vLmFpL2NsYWltcy9waG9uZSI6bnVsbCwiaWF0IjoxNzI5NjM0ODk3LCJpc3MiOiJodHRwczovL2NsZXJrLnN1bm8uY29tIiwianRpIjoiNjVmMzE1MThhMmYxYTFlYzA5YjkiLCJuYmYiOjE3Mjk2MzQ4ODcsInNpZCI6InNlc3NfMm1vNGhnVXF0Um94ck5lZXNFb1JEbmxrVjVtIiwic3ViIjoidXNlcl8yZW02QUV4S2tBTmc0SUoyVE0yUGkwM2N1S0sifQ.QaGRdyx7Im2KZUczjP7Rzb7ssJ9xwiqVJmSXplWKr4g_Hb62EimdzaZwfGtogTwMWY4VM7MEeSbN3gLxt5oS_WZ7YRCFjJManMQ78sySQiHAd9SXUVxGagVv_EwAs71Y04mH2GqZ69xPZGRl41mWfaTAkGe-pG3zektVn-0XyWI2KudAFsk0i9D1kxsGUFPPTwZ2RO8Vif_TzF-7jZEGgigVM2B_FnpezOOvAX3R9beqAJyvb0vjt5VT6a3rYRIQ4xrKC3K7uL9mqZJ6anYH8gk2Pb0CqFLU4CdLcqlwmeIMdlnCVhKGf5cpSLRsBx1NHtU64irl5FBCjfQNnZwnCg; mp_26ced217328f4737497bd6ba6641ca1c_mixpanel=%7B%22distinct_id%22%3A%20%220f18e5a5-4db7-467b-9148-24440d9fe249%22%2C%22%24device_id%22%3A%20%2219244b5b673822-0de651cefb6025-16525637-1fa400-19244b5b673822%22%2C%22utm_source%22%3A%20%22Klaviyo%22%2C%22utm_medium%22%3A%20%22campaign%22%2C%22utm_campaign%22%3A%20%22non-engaged%20users%20last%20call%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%2C%22%24user_id%22%3A%20%220f18e5a5-4db7-467b-9148-24440d9fe249%22%7D; _dd_s=rum=0&expire=1729635806671",
            "Content-Type": "application/json"
        }
        data = {
            "prompt": "Create a musical piece based on this audio input",
            "make_instrumental": True,
        }
        response = requests.post(SUNO_API_URL, json=data, headers=headers)       
        
    if response.status_code == 200:
        result = response.json()
        audio_url = result['audio_url']
        
        # Download the generated audio
        audio_response = requests.get(audio_url)
        if audio_response.status_code == 200:
            generated_filename = f"generated_music_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            with open(generated_filename, 'wb') as f:
                f.write(audio_response.content)
            print(f"Generated music saved as {generated_filename}")
            return generated_filename
    elif response.status_code == 503:
        print("Suno API is temporarily unavailable. Please try again later.")
        return None
    else:
        print(f"Error generating music: {response.status_code} - {response.text}")
        return None

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
                recorded_times = []
                start_time = time.time()
            elif stop_button.collidepoint(x, y):
                if recording:
                    recording = False
                    current_recording = save_recording()
                    if current_recording:
                        print(f"Recording saved as {current_recording}")
                        generated_music = generate_music_from_recording(current_recording)
                        if generated_music:
                            print(f"Generated music saved as {generated_music}")
                    else:
                        print("No sounds were recorded.")
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
