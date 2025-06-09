import os
import re
import string
import time
import threading
from threading import Event
from pynput.keyboard import Key, Listener
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

MODE = None

# --- Morse timing constants ---
DIT_LENGTH = 1
DAH_LENGTH = 3
INTRA_CHARACTER_SPACE_LENGTH = 1
INTER_CHARACTER_SPACE_LENGTH = 3
WORD_SPACE_LENGTH = 14

DIT_DURATION = 0.05  # base unit in seconds
DAH_DURATION = DAH_LENGTH * DIT_DURATION
INTRA_CHARACTER_SPACE_DURATION = INTRA_CHARACTER_SPACE_LENGTH * DIT_DURATION
INTER_CHARACTER_SPACE_DURATION = INTER_CHARACTER_SPACE_LENGTH * DIT_DURATION
WORD_SPACE_DURATION = WORD_SPACE_LENGTH * DIT_DURATION

# --- Morse code dictionary ---
MORSE_CODE = {
    '.-': 'A',
    '-...': 'B',
    '-.-.': 'C',
    '-..': 'D',
    '.': 'E',
    '..-.': 'F',
    '--.': 'G',
    '....': 'H',
    '..': 'I',
    '.---': 'J',
    '-.-': 'K',
    '.-..': 'L',
    '--': 'M',
    '-.': 'N',
    '---': 'O',
    '.--.': 'P',
    '--.-': 'Q',
    '.-.': 'R',
    '...': 'S',
    '-': 'T',
    '..-': 'U',
    '...-': 'V',
    '.--': 'W',
    '-..-': 'X',
    '-.--': 'Y',
    '--..': 'Z',
}

# --- Thread variables ---
playback_done = Event()

# --- Pygame variables ---
pygame.mixer.init()
beep_sound = pygame.mixer.Sound("beep.wav")

# --- State variables ---
press_time = None
last_release_time = None
morse_sequence = ''
output_buffer = ''

def update_durations():
    global DIT_DURATION, DAH_DURATION, INTRA_CHARACTER_SPACE_DURATION, INTER_CHARACTER_SPACE_DURATION, WORD_SPACE_DURATION

    DAH_DURATION = DAH_LENGTH * DIT_DURATION
    INTRA_CHARACTER_SPACE_DURATION = INTRA_CHARACTER_SPACE_LENGTH * DIT_DURATION
    INTER_CHARACTER_SPACE_DURATION = INTER_CHARACTER_SPACE_LENGTH * DIT_DURATION
    WORD_SPACE_DURATION = WORD_SPACE_LENGTH * DIT_DURATION

def menu():
    mode = None
    print("Choose a mode:")
    print("[1] - Live Translator")
    print("[2] - Train translating text")
    while True:
        mode = input("Enter 1 or 2: ").strip()
        if mode in ('1', '2'):
            return int(mode)
        print("Invalid choice. Please enter 1 or 2.")

# --- Print A-Z table
def print_table():
    print("╭", end='')
    for x in range(4):
        print("─" * 9 + "┬", end='')
    print("\b╮")
    items = list(MORSE_CODE.items())
    items.sort(key=lambda x: x[1])  # Sort by letter

    for i in range(0, len(items), 4):
        row = items[i:i+4]
        line = "│ "
        for code, letter in row:
            line += f"{letter}: {code:<4} │ "
        if len(row) < 4:
            line += "\b" + ((" " * 9) + "│") * 2
        print(line)
    print("╰", end='')
    for x in range(4):
        print("─" * 9 + "┴", end='')
    print("\b╯")

def print_speed():
    while True:
        print(f"\rSpeed: {DIT_DURATION:.2f} | Output: {output_buffer}", end='', flush=True)
        time.sleep(0.1)

# --- Handle key press ---
def on_press(key):
    global press_time, last_release_time, output_buffer, DIT_DURATION

    if key == Key.esc:
        return os._exit(0)
    if key == Key.up:
        DIT_DURATION += 0.01
        update_durations()
        # print(f"Speed: {DIT_DURATION:.2f}") # for non static Speed print
    if key == Key.down and DIT_DURATION > 0.01:
        DIT_DURATION -= 0.01
        update_durations()
        # print(f"Speed: {DIT_DURATION:.2f}") # for non static Speed print
    if MODE == 1:
        if key == Key.space:
            press_time = time.time()
            beep_sound.play(-1)  # loop indefinitely
            if last_release_time:
                idle_time = time.time() - last_release_time

                if idle_time >= WORD_SPACE_DURATION:
                    output_buffer += '/'
            last_release_time = None
        if key == Key.enter:
            print("\n")
            last_release_time = None
            output_buffer = ''
    else:
        if key == Key.space:
            output_buffer += '/'  # Interpret space as '/'
        if key == Key.backspace:
            output_buffer = output_buffer[:-1]
        elif hasattr(key, 'char') and key.char:
            c = key.char.upper()
            if c in string.ascii_uppercase:
                output_buffer += c

# --- Handle key release ---
def on_release(key):
    global press_time, last_release_time, morse_sequence

    if key == Key.space and press_time:
        release_time = time.time()
        beep_sound.stop()
        pressed_time = release_time - press_time
        press_time = None
        last_release_time = release_time

        if pressed_time < DAH_DURATION:
            morse_sequence += '.'
        else:
            morse_sequence += '-'

# --- Decode loop ---
def decode_loop():
    global last_release_time, morse_sequence, output_buffer

    while True:
        if last_release_time:
            idle_time = time.time() - last_release_time

            if idle_time >= INTER_CHARACTER_SPACE_DURATION:
                if morse_sequence:
                    decoded_char = MORSE_CODE.get(morse_sequence, '?')
                    output_buffer += decoded_char  # update buffer instead of printing
                    morse_sequence = ''

        time.sleep(0.1)

# --- Make text file readable ---
def normilize_txt(file):
    with open(file, 'r', encoding='utf-8') as f:
        text = f.read()

    # Convert to uppercase
    text = text.upper()

    # Replace all non-letter characters with slashes
    text = ''.join(char if char in string.ascii_uppercase else '/' for char in text)

    # Collapse multiple slashes into a single slash
    normalized = re.sub(r'/+', '/', text)

    # Remove trailing slashes
    normalized = normalized.rstrip('/')

    return normalized

# --- Play text ---
def play_txt(text):
    global DIT_DURATION, DAH_DURATION

    playback_done.clear()
    for char in text:
        if char == '/':
            time.sleep(WORD_SPACE_DURATION)
            continue

        morse = next((k for k, v in MORSE_CODE.items() if v == char), None)
        if not morse: # Skip unknown characters
            continue

        for symbol in morse:
            if symbol == '.':
                beep_sound.play()
                time.sleep(DIT_DURATION)
                beep_sound.stop()
            elif symbol == '-':
                beep_sound.play()
                time.sleep(DAH_DURATION)
                beep_sound.stop()
            time.sleep(INTRA_CHARACTER_SPACE_DURATION)
        time.sleep(INTER_CHARACTER_SPACE_DURATION - INTRA_CHARACTER_SPACE_DURATION)

    playback_done.set()

def compare_txt(normalized_txt):
    global output_buffer

    playback_done.wait()
    print("")
    if output_buffer == normalized_txt:
        print("[SUCCESS]")
    else:
        print("[ERROR] Your input does not match.\n")
        print("--- INPUT ---")
        print(output_buffer)
        print("--- EXCEPTED ---")
        print(normalized_txt)
    os._exit(0) # Immediate exit, bypass lingering listener

# --- Live translation ---
def mode_1():
    print_table()
    threading.Thread(target=print_speed, daemon=True).start()
    threading.Thread(target=decode_loop, daemon=True).start()

# --- Train translating Morse code from a text file ---
def mode_2():
    while True:
        file = input("Enter filename: ").strip()
        if os.path.exists(file):
            break
        else:
            print("[ERROR] '" + file + "' does not exist.")
    print_table()
    normalized_txt = normilize_txt(file)
    threading.Thread(target=print_speed, daemon=True).start()
    time.sleep(3) # wait time before start

    threading.Thread(target=play_txt, args=(normalized_txt,), daemon=True).start()
    threading.Thread(target=compare_txt, args=(normalized_txt,), daemon=True).start()

if __name__ == "__main__":
    MODE = int(menu())
    if MODE == 1:
        mode_1()
    else:
        mode_2()

    # --- Start listener ---
    with Listener(on_press=on_press, on_release=on_release, suppress=True) as listener:
        listener.join()
