import marshal
import os
import pickle
import sys
from array import array
from typing import Dict
from typing import Tuple
import heapq

# ------------------------- ENCODING -------------------------


def encode(message: bytes) -> Tuple[str, Dict]:
    """ Given the bytes read from a file, encodes the contents using the Huffman encoding algorithm.
    :param message: raw sequence of bytes from a file
    :returns: string of 1s and 0s representing the encoded message
              dict containing the decoder ring as explained in lecture and handout.
    """
    freq = freq_tree(message)
    freq_min_heap = freq_min_heap(freq)
    huffman_tree = huffman_tree(freq_min_heap)
    encoder_ring = encoder_ring(huffman_tree)
    
    # encoded_bytes = "".join([codes[byte] for byte in message])
    encoded_bytes = ""
    for byte in message:
        encoded_bytes += encoder_ring[byte]

    return encoded_bytes


def freq_tree(message: bytes) -> Dict:
    """ Given the bytes read from a file, returns a dictionary containing the frequency of each byte in the file.

    :param message: raw sequence of bytes from a file
    :returns: dict containing the frequency of each byte in the file
    """
    return {byte: message.count(byte) for byte in set(message)}


def freq_min_heap(freq: Dict) -> list:
    """ Given a dictionary containing the frequency of each byte in a file, returns a minheap containing the frequency tree for each byte.

    :param freq: dict containing the frequency of each byte in a file
    :returns: minheap containing the frequency tree for each byte
    """
    # freq_min_heap = []
    # for k, v in freq.items():
    #     heapq.heappush(freq_min_heap, (v, k))
    freq_min_heap = [(v, k) for k, v in freq.items()]
    heapq.heapify(freq_min_heap)
    return freq_min_heap


def huffman_tree(freq_min_heap: list):
    """ Given a minheap containing the frequency tree for each byte, returns a huffman tree.

    :param minheap: minheap containing the frequency tree for each byte
    :returns: huffman tree
    """
    # Repeat until there is only one node left in the minheap
    while len(freq_min_heap) > 1:
        # Pop the two smallest frequencies from the minheap
        left = heapq.heappop(freq_min_heap)
        right = heapq.heappop(freq_min_heap)

        # Create a new node with the sum of the two frequencies as the frequency,
        # and add the two smallest frequencies as children to the new node,
        new = (left[0] + right[0], left, right)

        # Add the new node to the minheap
        heapq.heappush(freq_min_heap, new)

    return freq_min_heap[0]


def encoder_ring(huffman_tree) -> Dict:
    """ Given a huffman tree, returns an encoder ring.

    :param message: raw sequence of bytes from a file
    :returns: string of 1s and 0s representing the encoded message
              dict containing the decoder ring as explained in lecture and handout.
    """
    codes = {}
    def _encoder_ring(node: Tuple[int, any, any], code: str):
        # If a node has only one child, its left child is a leaf node
        # so we can add that code to the dictionary
        if len(node) == 2:
            codes[node[1]] = code
        else:
            _encoder_ring(node[1], code + '0')
            _encoder_ring(node[2], code + '1')
    _encoder_ring(huffman_tree, '')
    return codes

# ------------------------- DECODING -------------------------


def decode(message: str, decoder_ring: Dict) -> bytes:
    """ Given the encoded string and the decoder ring, decodes the message using the Huffman decoding algorithm.

    :param message: string of 1s and 0s representing the encoded message
    :param decoder_ring: dict containing the decoder ring
    return: raw sequence of bytes that represent a decoded file
    """
    raise NotImplementedError


def compress(message: bytes) -> Tuple[array, Dict]:
    """ Given the bytes read from a file, calls encode and turns the string into an array of bytes to be written to disk.

    :param message: raw sequence of bytes from a file
    :returns: array of bytes to be written to disk
              dict containing the decoder ring
    """
    return encode(message)


def decompress(message: array, decoder_ring: Dict) -> bytes:
    """ Given a decoder ring and an array of bytes read from a compressed file, turns the array into a string and calls decode.

    :param message: array of bytes read in from a compressed file
    :param decoder_ring: dict containing the decoder ring
    :return: raw sequence of bytes that represent a decompressed file
    """
    raise NotImplementedError


# ------------------------- MAIN -------------------------
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
