from pynput.keyboard import Key, Listener
import time
import threading

# --- Morse timing constants ---
DIT_LENGTH = 1
DAH_LENGTH = 3
INTRA_CHARACTER_SPACE_LENGTH = 1
INTER_CHARACTER_SPACE_LENGTH = 3
WORD_SPACE_LENGTH = 7

DIT_DURATION = 0.05  # base unit in seconds
DAH_DURATION = DAH_LENGTH * DIT_DURATION
INTRA_CHARACTER_SPACE_DURATION = INTRA_CHARACTER_SPACE_LENGTH * DIT_DURATION
INTER_CHARACTER_SPACE_DURATION = INTER_CHARACTER_SPACE_LENGTH * DIT_DURATION
WORD_SPACE_DURATION = WORD_SPACE_LENGTH * DIT_DURATION
OFFSET_DURATION = DIT_DURATION

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

# --- Handle key press ---
def on_press(key):
    global press_time, last_release_time
    if key == Key.space:
        press_time = time.time()
        if last_release_time:
            idle_time = time.time() - last_release_time

            if idle_time >= WORD_SPACE_DURATION:
                print('/', end='', flush=True)
        last_release_time = None

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

        # Round to nearest dit unit

        if pressed_time < DAH_DURATION - OFFSET_DURATION:
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
                    print(decoded_char, end='', flush=True)
                    morse_sequence = ''

        time.sleep(DIT_DURATION)

# --- Print A-Z table
def print_table():
    print(" ", end='')
    print("_" * (10 * 4 - 1))
    items = list(MORSE_CODE.items())
    items.sort(key=lambda x: x[1])  # Sort by letter

    for i in range(0, len(items), 4):
        row = items[i:i+4]
        line = "| "
        for code, letter in row:
            line += f"{letter}: {code:<4} | "
        print(line)
    print(" ", end='')
    print("_" * (10 * 4 - 1))

if __name__ == "__main__":
    print_table()
    print("\nInput: ", end='')
    threading.Thread(target=decode_loop, daemon=True).start()

# --- Start listener ---
with Listener(on_press=on_press, on_release=on_release, suppress=True) as listener:
    listener.join()
