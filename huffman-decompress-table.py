import marshal
import os
import pickle
import sys
from array import array
from typing import Dict
from typing import Tuple
import heapq
from collections import defaultdict, deque

# ------------------------- ENCODING -------------------------

def create_huffman_tree(message: bytes) -> Dict:
    # Use a dict to store the frequency of each byte and its priority
    # key: byte, value: (frequency, priority)
    byte_freqs = defaultdict(lambda: (0, 0))
    priority = 0
    
    for byte in message: # O(n)
        # Assign each byte a priority on a first come first serve basis
        # The more frequent a byte is and the sooner it is read, the higher its priority.
        # Increment the frequency of the byte and decrement its priority
        byte_freqs[byte] = (byte_freqs[byte][0] + 1,
                            byte_freqs[byte][1] - priority)
        priority += 1

    # Create minheap of tuples of (freq, priority, byte)
    freq_min_heap = []
    for byte, (freq, priority) in byte_freqs.items(): # O(nlog(n))
        heapq.heappush(freq_min_heap, (freq, priority, byte))

    # Repeat until there is only one node left in the minheap
    while len(freq_min_heap) > 1: # O(nlog(n))
        # Pop the two smallest frequencies from the minheap
        left = heapq.heappop(freq_min_heap)
        right = heapq.heappop(freq_min_heap)

        # Create a new node as (sum of freqs, sum of priorities, left child, right child)
        new = (left[0] + right[0], left[1] + right[1], left, right)

        # Add the new node to the minheap
        heapq.heappush(freq_min_heap, new)

    return freq_min_heap[0]


def create_decoder_ring(huffman_tree) -> Dict:
    """ Given a huffman tree, returns an encoder ring.

    :param message: raw sequence of bytes from a file
    :returns: string of 1s and 0s representing the encoded message
              dict containing the decoder ring as explained in lecture and handout.
    """
    decoder_ring = {}  # key: byte, value: code
    # Leaf nodes: (freq, prority, byte)
    # Parent nodes: (freq, priority, left child, right child)
    # Each element in the stack is a tuple (node, code)
    stack = deque([(huffman_tree, '')])
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
    huffman_tree = create_huffman_tree(message)
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
    byte = ""
    for bit in encoded_message:
        # Shift byte left by 1, and add curr bit to end
        byte += bit

        # If byte is full, add it to compressed message, and clear byte
        if len(byte) == 8:
            compressed_message.append(int(byte, 2))
            byte = ""

    # If there is a partial byte left, pad the right with 0s,
    # add the amount padded as a key to the decoder ring,
    # then add the padded bit to the compressed message
    if len(byte) != 0:
        padded_byte = byte
        pad_count = 0
        while len(padded_byte) < 8:
            padded_byte += '0'
            pad_count += 1

        compressed_message.append(int(padded_byte, 2))
        decoder_ring['pad_count'] = pad_count

    return (compressed_message, decoder_ring)

# ------------------------- DECODING -------------------------


def decode(message: str, decoder_ring: Dict) -> bytes:
    """ Given the encoded string and the decoder ring, decodes the message using the Huffman decoding algorithm.

    :param message: string of 1s and 0s representing the encoded message
    :param decoder_ring: dict containing the decoder ring
    return: raw sequence of bytes that represent a decoded file
    """

    decoded_message = array('B')
    buf = 0
    table = [None] * 256

    for byte, code in decoder_ring.items():
        table[byte] = int(code) % 256

    # Convert message string to sequence of integers
    message_ints = [int(bit) for bit in message]

    for bit in message_ints:
        buf = (buf << 1) | bit  # Shift the bits to the left and add the new bit
        if table[buf] is not None:
            decoded_message.append(table[buf])
            buf = 0


    return bytes(decoded_message)


def decompress(message: array, decoder_ring: Dict) -> bytes:
    """ Given a decoder ring and an array of bytes read from a compressed file, turns the array into a string and calls decode.

    :param message: array of bytes read in from a compressed file
    :param decoder_ring: dict containing the decoder ring
    :return: raw sequence of bytes that represent a decompressed file
    """
    decompressed_message = ""

    byte_index = 0
    for byte in message:
        decompressed_message += bin(byte)[2:].zfill(8)
        if 'pad_count' in decoder_ring and byte_index == len(message) - 2:
            break
        byte_index += 1

    if 'pad_count' in decoder_ring:
        # Need to remove the padding from the last byte
        pad_count = decoder_ring['pad_count']
        del decoder_ring['pad_count']
        padded_byte = bin(message[len(message) - 1])[2:]

        # Add back 0s if pad_count + the unpadded byte length is less than 8
        unpadded_byte = padded_byte[:-pad_count].zfill(8 - pad_count)

        decompressed_message += unpadded_byte

    return decode(decompressed_message, decoder_ring)


# ------------------------- MAIN -------------------------
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
