import marshal
import os
import pickle
import sys
from array import array
from typing import Dict
from typing import Tuple
import heapq
from collections import defaultdict
import random

# ------------------------- ENCODING -------------------------


def get_byte_freqs(message: bytes) -> Dict:
    """ Given the bytes read from a file, returns a dictionary containing the frequency of each byte in the file.

    :param message: raw sequence of bytes from a file
    :returns: dict containing the frequency of each byte in the file, key: byte, value: frequency
    """
    return {byte: message.count(byte) for byte in set(message)} # key: byte, value: frequency


def create_huffman_tree(byte_freqs: dict):
    """ Given a minheap containing the frequency tree for each byte, returns a huffman tree.

    :param minheap: minheap containing the frequency tree for each byte
    :returns: huffman tree
    """
    # Ensure all elements in the minheap are tuples with the frequency as the first element
    freq_min_heap = [(freq, byte)
                     for byte, freq in byte_freqs.items()]

    # Build the min heap
    heapq.heapify(freq_min_heap)

    # Give each node a priority, the higher the frequency, the higher the priority
    # print("before priorites:", freq_min_heap)
    priority_min_heap = []
    priority = len(freq_min_heap)
    while freq_min_heap:
        node = heapq.heappop(freq_min_heap)
        # print("node:", node)
        priority_min_heap.append((node[0], priority, node[1]))
        priority -= 1
    

    heapq.heapify(priority_min_heap)
    # print("after priorites:", priority_min_heap)

    priority = 0
    # Repeat until there is only one node left in the minheap
    while len(priority_min_heap) > 1:
        # Pop the two smallest frequencies from the minheap
        # print("left:", freq_min_heap[0])
        # print("right:", freq_min_heap[1])
        left = heapq.heappop(priority_min_heap)
        right = heapq.heappop(priority_min_heap)

        # Create a new node with the sum of the two frequencies as the frequency,
        # and add the two smallest frequencies as children to the new node,
        # (freq sum, left child, right child)
        # TODO: Need to also add a priority to the new node, but what should it be?
        # What causes the bad comparison error for tuple to int is there are two different nodes with the same frequency sum,
        # to the heapq tries to compare the next element in the tuple, which is a tuple

        # NOTE: What if I just make it so the higher the frequency, the higher the priority?
        priority = left[1] - right[1]
        new = (left[0] + right[0], priority, left, right)

        # Add the new node to the minheap
        heapq.heappush(priority_min_heap, new)

    return priority_min_heap[0]


def create_decoder_ring(huffman_tree) -> Dict:
    """ Given a huffman tree, returns an encoder ring.

    :param message: raw sequence of bytes from a file
    :returns: string of 1s and 0s representing the encoded message
              dict containing the decoder ring as explained in lecture and handout.
    """
    decoder_ring = {}  # key: byte, value: code

    # print(huffman_tree)

    # Leaf nodes: (freq, prority, byte)
    # Parent nodes: (freq, priority, left child, right child)

    def _create_decoder_ring(node, code: str):
        # print("node:", node)

        # If the node is a parent node, recursively call the function on its children
        # and add 0 to code for the left child and 1 for the right child
        if isinstance(node[2], int):
            # print("Leaf!")
            # print("Adding code:", node[2], ":", code, "\n")
            decoder_ring[node[2]] = code
        else:
            # print("Parent!")
            # print("left child:", node[1])
            # print("right child:", node[2], "\n")
            _create_decoder_ring(node[2], code + '0')
            _create_decoder_ring(node[3], code + '1')

    _create_decoder_ring(huffman_tree, '')

    # print("decoder_ring:", decoder_ring)

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
    buf = ''
    flipped_decoder = {v: k for k, v in decoder_ring.items()}

    for bit in message:
        buf += bit
        if buf in flipped_decoder:
            decoded_message.append(flipped_decoder[buf])
            buf = ''

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
        padded_byte = bin(message[len(message) - 1])[2:]

        # Add back 0s if pad_count + the unpadded byte length is less than 8
        unpadded_byte = padded_byte[:-pad_count].zfill(8 - pad_count)

        decompressed_message += unpadded_byte

    return decode(decompressed_message, decoder_ring)


# ------------------------- MAIN -------------------------
# -v : encode
# w : decode
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
