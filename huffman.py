import marshal
import os
import pickle
import sys
from array import array
from typing import Dict, Tuple
import heapq
from collections import defaultdict, deque

''' INVARIANTS
Encoding
Initialization: A raw sequence of bytes from a file.
Maintenance: During construction of the huffman tree, there are three invariants that must be maintained:
1. The frequency of each byte must be maintained in order to decide its order in the minheap and correctly calculate the prefix code based on its frequency.
2. Each prefix code is unique to a byte.
3. The more a byte occurs in the file, the shorter its prefix code is to maximize compression.
    - Traversing the minheap tree left adds a 0 to the prefix code, and traversing right adds a 1.
Termination: Termination is reached when all bytes in the file have been encoded with a unique prefix code.

Decoding
Initialization: a raw sequence of already compressed bytes from a file, encoded and compressed using its matching encode and compression functions and 
a decoder ring where key = byte, value = code.
Maintenance: During decoding, the invariant that must be maintained is that the decoder ring must have a code for each byte in the message.
Termination: Termination is reached when all bytes in the message have been decoded into their original bytes.
'''


# ------------------------- Encoding -------------------------

def get_byte_freqs(message: bytes) -> Dict:
    """ Given the bytes read from a file, returns a dictionary containing the frequency and priority of each byte in the file.
    :param message: raw sequence of bytes from a file
    :returns: dict of tuples containing the frequency and priority of each byte in the file
    """
    byte_freqs = defaultdict(lambda: (0, 0)) # key: byte, value: (frequency, priority)
    priority = 0
    for byte in message:  # O(n)
        # Increment frequency, and assign priority on first come first serve basis
        byte_freqs[byte] = (byte_freqs[byte][0] + 1,
                            byte_freqs[byte][1] - priority)
        priority += 1

    return byte_freqs


def create_huffman_tree(byte_freqs: Dict) -> Tuple:
    """ Given a dict containing the frequency and priority of each byte, returns a huffman tree.
    :param byte_freqs: dict of tuples containing the frequency and priority for each byte
    :returns: huffman tree
    """

    # Create minheap of tuples (freq, priority, byte)
    freq_min_heap = []
    for byte, (freq, priority) in byte_freqs.items():  # O(nlog(n))
        heapq.heappush(freq_min_heap, (freq, priority, byte))

    # Construct tree until there is only one node left in the minheap
    while len(freq_min_heap) > 1:  # O(nlog(n))
        # Pop the two smallest frequencies from the minheap
        left = heapq.heappop(freq_min_heap)
        right = heapq.heappop(freq_min_heap)
        # Add a new node as (sum of freqs, sum of priorities, left child, right child)
        new = (left[0] + right[0], left[1] + right[1], left, right)
        heapq.heappush(freq_min_heap, new)

    return freq_min_heap[0]


def create_decoder_ring(huffman_tree: Tuple) -> Dict:
    """ Given a huffman tree, returns an encoder ring.

    :param message: raw sequence of bytes from a file
    :returns: string of 1s and 0s representing the encoded message
              dict containing the decoder ring as explained in lecture and handout.
    """
    decoder_ring = {}  # key: byte, value: code

    # Leaf nodes  : (freq, prority, byte)
    # Parent nodes: (freq, priority, left child, right child)
    # Each element in the stack is a tuple (node, code)
    stack = deque([(huffman_tree, '')]) # O(1) pop and append
    # Construct huffman tree iteratively using a stack
    while stack:
        current_node, code = stack.pop()
        if isinstance(current_node[2], int):
            # If the node is a leaf node, add the byte and code to the decoder ring
            decoder_ring[current_node[2]] = code

        else:
            # If the node is a parent node, add its children to the stack
            # and add 0 to code for the left child and 1 for the right child
            stack.append((current_node[2], code + '0'))
            stack.append((current_node[3], code + '1'))

    return decoder_ring


def encode(message: bytes) -> Tuple[str, Dict]:
    """ Given the bytes read from a file, encodes the contents using the Huffman encoding algorithm.
    :param message: raw sequence of bytes from a file
    :returns: string of 1s and 0s representing the encoded message
              dict containing the decoder ring as explained in lecture and handout.
    """
    byte_freqs = get_byte_freqs(message)
    huffman_tree = create_huffman_tree(byte_freqs)
    decoder_ring = create_decoder_ring(huffman_tree)
    encoded_message = ''.join([decoder_ring[byte] for byte in message])

    return (encoded_message, decoder_ring)


def compress(message: bytes) -> Tuple[array, Dict]:
    """ Given the bytes read from a file, calls encode and turns the string into an array of bytes to be written to disk.

    :param message: raw sequence of bytes from a file
    :returns: array of bytes to be written to disk
              dict containing the decoder ring
    """
    encoded_message, decoder_ring = encode(message)
    compressed_message = array('B')
    byte = 0
    bit_count = 0
    for bit in encoded_message:
        # Shift byte left by 1, and add curr bit to end
        byte = (byte << 1) | int(bit)
        bit_count += 1
        # If byte is full, add it to compressed message, and clear byte
        if bit_count == 8:
            compressed_message.append(byte)
            byte = 0
            bit_count = 0

    # If there is a partial byte left, pad the right with 0s,
    # add the amount padded as a key to the decoder ring,
    # then add the padded bit to the compressed message
    if bit_count > 0:
        pad_count = 8 - bit_count
        byte <<= pad_count
        compressed_message.append(byte)
        decoder_ring['pad_count'] = pad_count

    return (compressed_message, decoder_ring)


# ------------------------- Decoding -------------------------

def decode(message: str, decoder_ring: Dict) -> bytes:
    """ Given the encoded string and the decoder ring, decodes the message using the Huffman decoding algorithm.

    :param message: string of 1s and 0s representing the encoded message
    :param decoder_ring: dict containing the decoder ring
    return: raw sequence of bytes that represent a decoded file
    """
    flipped_decoder = {code: byte for byte, code in decoder_ring.items()} # O(n)
    # Precompute the set of keys in the flipped_decoder for faster membership checking, because very large dicts are slow
    flipped_decoder_keys = set(flipped_decoder.keys()) # O(n)

    decoded_message = array('B')
    buf = ""
    # Add bits to the buffer until the buffer is a key in the decoder ring
    for bit in message: # O(n)
        buf += bit
        if buf in flipped_decoder_keys:
            decoded_message.append(flipped_decoder[buf])
            buf = ""

    return bytes(decoded_message)


def decompress(message: array, decoder_ring: Dict) -> bytes:
    """ Given a decoder ring and an array of bytes read from a compressed file, turns the array into a string and calls decode.

    :param message: array of bytes read in from a compressed file
    :param decoder_ring: dict containing the decoder ring
    :return: raw sequence of bytes that represent a decompressed file
    """
    # Check if pad count exists in the decoder ring, else set to False
    pad_count = decoder_ring.pop('pad_count', False)

    # Add each raw byte in message to string
    decompressed_message = ""
    byte_index = 0
    for byte in message: # O(n)
        decompressed_message += bin(byte)[2:].zfill(8)
        # Save the last byte if there is a pad count
        if pad_count and byte_index == len(message) - 2:
            break
        byte_index += 1

    if pad_count:
        # Remove all trailing 0s from last byte
        padded_byte = bin(message[len(message) - 1])[2:]
        # Add back 0s that are part of the codes
        unpadded_byte = padded_byte[:-pad_count].zfill(8 - pad_count)
        decompressed_message += unpadded_byte

    return decode(decompressed_message, decoder_ring)


# ------------------------- Main -------------------------
# -v: encode, w: decode , -c  compress, -d: decompress
if __name__ == '__main__':
    usage = f'Usage: {sys.argv[0]} [ -c | -d | -v | -w ] infile outfile'
    if len(sys.argv) != 4:
        raise Exception(usage)

    operation = sys.argv[1]
    if operation not in {'-c', '-d', '-v', 'w'}:
        raise Exception(usage)

    infile, outfile = sys.argv[2], sys.argv[3]
    if not os.path.exists(infile):
        raise FileExistsError(f'{infile} does not exist.')

    if operation in {'-c', '-v'}:
        with open(infile, 'rb') as fp:
            _message = fp.read()

        if operation == '-c':
            _message, _decoder_ring = compress(_message)
            with open(outfile, 'wb') as fp:
                marshal.dump((pickle.dumps(_decoder_ring), _message), fp)
        else:
            _message, _decoder_ring = encode(_message)
            print(_message)
            with open(outfile, 'wb') as fp:
                marshal.dump((pickle.dumps(_decoder_ring), _message), fp)

    else:
        with open(infile, 'rb') as fp:
            pickleRick, _message = marshal.load(fp)
            _decoder_ring = pickle.loads(pickleRick)

        if operation == '-d':
            bytes_message = decompress(array('B', _message), _decoder_ring)
        else:
            bytes_message = decode(_message, _decoder_ring)
        with open(outfile, 'wb') as fp:
            fp.write(bytes_message)
