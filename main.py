from pynput.keyboard import Key, Listener
import math
import time
import threading

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

# --- Handle key press ---
def on_press(key):
    global press_time, last_release_time, output_buffer, DIT_DURATION

    if key == Key.up:
        DIT_DURATION += 0.01
        update_durations()
        # print(f"Speed: {DIT_DURATION:.2f}") # for non static Speed print
    if key == Key.down and DIT_DURATION > 0.01:
        DIT_DURATION -= 0.01
        update_durations()
        # print(f"Speed: {DIT_DURATION:.2f}") # for non static Speed print
    if key == Key.space:
        press_time = time.time()
        if last_release_time:
            idle_time = time.time() - last_release_time

            if idle_time >= WORD_SPACE_DURATION:
                output_buffer += '/'
        last_release_time = None
    if key == Key.enter:
        print("\n")
        last_release_time = None
        output_buffer = ''

# --- Handle key release ---
def on_release(key):
    global press_time, last_release_time, morse_sequence

    if key == Key.esc:
        return False  # stop listener

    if key == Key.space and press_time:
        release_time = time.time()
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

if __name__ == "__main__":
    print_table()
    threading.Thread(target=print_speed, daemon=True).start()
    threading.Thread(target=decode_loop, daemon=True).start()

# --- Start listener ---
with Listener(on_press=on_press, on_release=on_release, suppress=True) as listener:
    listener.join()
