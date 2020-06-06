'''
Control library for the MAX6921 VFD controller
For use with CircuitPython
Not an official CircuitPython library
https://github.com/DellaHall

Digits and segments are lists of tuples:
[(cs pin, pin number), (board.d0, 1), ...]
'''

import board
import busio

class VFD():
    def __init__(self, digits, segments):
        self._chips = []
        # Create a list of the cs pins for each chip in use
        for chip, _ in digits:
            if chip not in self._chips:
                self._chips.append(chip)
        for chip, _ in segments:
            if chip not in self._chips:
                self._chips.append(chip)
        # Initialize all chips
        for chip in self._chips:
            chip.value = True
        # Build dictionaries for digit and segment pin values
        self._digits, self._segments = pin_legend(digits, segments, self._chips)
        self._size = len(self._digits)
        # Get character map
        self._charmap = build_charmap(self._segments)
        self.print(" trans.rights")
        # Initiate SPI
        self._spi = busio.SPI(board.SCK, MOSI=board.MOSI)

    def init_spi(self, clock, data):
        '''Initialize SPI'''
        self._clock = clock
        self._data = data
        self._spi = busio.SPI(self._clock, MOSI=self._data)
        while not self._spi.try_lock():
            pass
        self._spi.configure(baudrate=5000000, phase=0, polarity=0, bits=8)
        self._spi.unlock()

    def print(self, text):
        '''Outputs text to the display'''
        self._print_buffer = str(text).upper()
        # Pad out the text with a space
        # This helps avoid one bright character at the end of the line
        self._print_buffer += " "

    def draw(self):
        '''Call once per server loop to update the display'''
        offset = 0
        for digit in range(self._size):
            # Concats the digit pin with all the segment pins
            try:
                # Add an offset if this character is a period
                if self._print_buffer[digit + offset] == ".":
                    offset += 1
                character = concat(self._digits[digit], 
                  self._charmap[self._print_buffer[digit + offset]])
                # If the next character is a period, display it on this character
                if self._print_buffer[digit + offset + 1] == ".":
                    character = concat(character, self._charmap["."])
                # If this character is a space, we can skip it
                if self._print_buffer[digit + offset] == " ":
                    continue
            except IndexError:
                # If we're out of text to display, we don't need to do anything
                pass
            for chip in range(len(self._chips)):
                while not self._spi.try_lock():
                    pass
                self._chips[chip].value = False
                self._spi.write(bytes(character[chip]))
                self._chips[chip].value = True
                self._spi.unlock()

def pin_legend(digits, segments, chips):
    '''Builds dictionaries for knowing which pins to use when'''
    # Digit definitions
    out_digits = {}
    for i in range(len(digits)):
        temp_chips = [[0, 0, 0] for _ in range(len(chips))]
        chip_index = chips.index(digits[i][0])
        # Bits are written in reverse order 19-0
        # So the pin numbers need to be reversed
        # We also have to send 24 bits
        true_order = abs(digits[i][1] - 23)
        # Determine which byte is getting changed
        temp_bytes = [0, 0, 0]
        target_byte = true_order // 8
        # Create an empty byte
        temp_bits = ""
        target_bit = true_order % 8
        # Populate that byte with appropriate bits
        for j in range(8):
            if j == target_bit:
                temp_bits += "1"
            else:
                temp_bits += "0"
        # Write the bits into the right byte as a bin number
        temp_bytes[target_byte] = int(temp_bits, 2)
        temp_chips[chip_index] = temp_bytes
        out_digits[i] = temp_chips

    # Segment definitions
    out_segments = {}
    # H is period
    # Extra letters can be added if your display has extra segments
    # Remember to update build_charmap() so those segments can be used
    segment_order = "ABCDEFGH"
    for i in range(len(segments)):
        temp_chips = [[0, 0, 0] for _ in range(len(chips))]
        chip_index = chips.index(digits[i][0])
        # Bits are written in reverse order 19-0
        # So the pin numbers need to be reversed
        # We also have to send 24 bits
        true_order = abs(segments[i][1] - 23)
        # Determine which byte is getting changed
        temp_bytes = [0, 0, 0]
        target_byte = true_order // 8
        # Create an empty byte
        temp_bits = ""
        target_bit = true_order % 8
        # Populate that byte with appropriate bits
        for j in range(8):
            if j == target_bit:
                temp_bits += "1"
            else:
                temp_bits += "0"
        # Write the bits into the right byte as a bin number
        temp_bytes[target_byte] = int(temp_bits, 2)
        temp_chips[chip_index] = temp_bytes
        out_segments[segment_order[i]] = temp_chips

    return out_digits, out_segments

def concat(*args):
    '''Concatenates pins so that a full character can be lit up at once'''
    arg_count = len(args)
    chip_count = len(args[0])
    byte_count = len(args[0][0])
    # Build an empty set of bytes
    output = []
    for _ in args[0]:
        output.append([0, 0, 0])
    # Go thru each chip in the input
    for i in range(arg_count):
        for j in range(chip_count):
            for k in range(byte_count):
                # Add the value to the appropriate byte
                output[j][k] += args[i][j][k]
                # It shouldn't be possible to get a value above 255
                # But the mod 256 will prevent crashing if it does happen
                output[j][k] %= 256
    return output

def build_charmap(segments):
    '''Returns a dictionary with a bitfield map for each printable character'''
    # Definition of which segments make up each character
    segment_dict = {
        "0": "DEFABC",
        "1": "BC",
        "2": "ABGED",
        "3": "ABGCD",
        "4": "FGBC",
        "5": "AFGCD",
        "6": "AFEDCG",
        "7": "ABC",
        "8": "AFBGECD",
        "9": "GFABCD",
        "A": "EGFABC",
        "B": "FEDCG",
        "C": "AFED",
        "D": "GEDCB",
        "E": "AFGED",
        "F": "AFGE",
        "G": "AFEDC",
        "H": "FGEC",
        "I": "FE",
        "J": "EDCB",
        "K": "AFEGC",
        "L": "FED",
        "M": "EGAC",
        "N": "EFABC",
        "O": "ABCDEF",
        "P": "EFABG",
        "Q": "GFABC",
        "R": "EFAB",
        "S": "AFGCD",
        "T": "FGED",
        "U": "FEDCB",
        "V": "FDCB",
        "W": "FDBG",
        "X": "FGBEC",
        "Y": "FGBCD",
        "Z": "ABGED",
        "-": "G",
        "_": "D",
        "^": "FAB",
        "*": "GFAB",
        "~": "A",
        "`": "F",
        "'": "B",
        "@": "ABCDEG",
        ":": "DG",
        ";": "DCG",
        "=": "GA",
        '"': "FB",
        "!": "BH",
        "?": "ABGEH",
        ".": "H",
        ",": "DC",
        "<": "GFA",
        ">": "ABG",
        "[": "DEFA",
        "]": "DCBA",
        "/": "BGE",
        "\\": "FGC",
        " ": ""
        }
    output = {}
    for key, value in segment_dict.items():
        # Build an empty set of bytes
        output[key] = list([0, 0, 0] for _ in range(len(segments["A"])))
        # Get list of all segments in character
        all_segments = list(segments[seg] for seg in value)
        # If there are segments, concatenate
        if all_segments:
            for segment in all_segments:
                output[key] = concat(output[key], segment)
    return output
