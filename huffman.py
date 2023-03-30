import marshal
import os
import pickle
import sys
from array import array
from typing import Dict
from typing import Tuple
import heapq

# ------------------------- ENCODING -------------------------


def create_freq_tree(message: bytes) -> Dict:
    """ Given the bytes read from a file, returns a dictionary containing the frequency of each byte in the file.

    :param message: raw sequence of bytes from a file
    :returns: dict containing the frequency of each byte in the file
    """
    return {byte: message.count(byte) for byte in set(message)}


def create_freq_min_heap(freq: Dict) -> list:
    """ Given a dictionary containing the frequency of each byte in a file, returns a minheap containing the frequency tree for each byte.

    :param freq: dict containing the frequency of each byte in a file
    :returns: minheap containing the frequency tree for each byte
    """
    freq_min_heap = [(v, k) for k, v in freq.items()]
    heapq.heapify(freq_min_heap)
    return freq_min_heap


def create_huffman_tree(freq_min_heap: list):
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


def create_decoder_ring(huffman_tree) -> Dict:
    """ Given a huffman tree, returns an encoder ring.

    :param message: raw sequence of bytes from a file
    :returns: string of 1s and 0s representing the encoded message
              dict containing the decoder ring as explained in lecture and handout.
    """
    decoder_ring = {}  # key: byte, value: code

    def _create_decoder_ring(node: Tuple[int, any, any], code: str):
        # If a node has only one child, its left child is a leaf node
        # so we can add that code to the dictionary
        if len(node) == 2:
            decoder_ring[node[1]] = code
        else:
            # if traversing left add 0
            _create_decoder_ring(node[1], code + '0')
            # if traversing right add 1
            _create_decoder_ring(node[2], code + '1')

    _create_decoder_ring(huffman_tree, '')

    # DEBUG
    print("decoder_ring:")
    for k, v in decoder_ring.items():
        print(chr(k), v)

    return decoder_ring


def encode(message: bytes) -> Tuple[str, Dict]:
    """ Given the bytes read from a file, encodes the contents using the Huffman encoding algorithm.
    :param message: raw sequence of bytes from a file
    :returns: string of 1s and 0s representing the encoded message
              dict containing the decoder ring as explained in lecture and handout.
    """
    freq_tree = create_freq_tree(message)
    freq_min_heap = create_freq_min_heap(freq_tree)
    huffman_tree = create_huffman_tree(freq_min_heap)
    decoder_ring = create_decoder_ring(huffman_tree)
    encoded_message = ''.join([decoder_ring[byte] for byte in message])

    # DEBUG
    print("\nencoded_message:", encoded_message, "\n")

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
    # DEBUG
    print("bytes appended to compressed_message:")
    for bit in encoded_message:
        # Shift byte left by 1, and add curr bit to end
        byte += bit

        # If byte is full, add it to compressed message, and clear byte
        if len(byte) == 8:
            # DEBUG
            print(byte)
            compressed_message.append(int(byte, 2))
            byte = ""

    # If there is a partial byte left, pad the right with 0s,
    # add the amount padded as a key to the decoder ring,
    # then add the padded bit to the compressed message

    # DEBUG
    # print("\ncompressed_message bytes w/o padding:", end=" ")
    # for byte in compressed_message:
    #     print(bin(byte)[2:], end="")
    # print("\nleftover byte to pad:", bin(byte)[2:])

    if len(byte) != 0:
        padded_byte = byte
        # DEBUG
        print("padded_byte before padding:", padded_byte)
        pad_count = 0
        while len(padded_byte) < 8:
            padded_byte += '0'
            pad_count += 1

        # DEBUG
        print("\npad_count:", pad_count)
        print("padded_byte after padding:", padded_byte)
        print("appending byte to compressed_message:", padded_byte)

        compressed_message.append(int(padded_byte, 2))
        decoder_ring['pad_count'] = pad_count

    # DEBUG
    print("\ncompressed_message bytes w/ padding:")
    for byte in compressed_message:
        print(bin(byte)[2:])

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

    # DEBUG
    print("\ndecoded_message:", end=" ")
    for byte in decoded_message:
        print(chr(byte), end="")

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
        # TODO: Don't append last byte if it is padded
        # DONE: Added if statement to check if byte_index is the last byte
        if 'pad_count' in decoder_ring and byte_index == len(message) - 2:
            break
        byte_index += 1

    # DEBUG
    if 'pad_count' in decoder_ring:
        print("\ndecompressed_message bytes w/o padded byte:", decompressed_message)

    if 'pad_count' in decoder_ring:
        # DEBUG
        print("\npad_count:", decoder_ring['pad_count'])

        # Need to remove the padding from the last byte
        pad_count = decoder_ring['pad_count']
        padded_byte = bin(message[len(message) - 1])[2:]

        # DEBUG
        print("padded_byte:", padded_byte)

        unpadded_byte = padded_byte[:-pad_count]

        # DEBUG
        print("unpadded_byte:", unpadded_byte)

        decompressed_message += unpadded_byte

    # DEBUG
    print("\ndecompressed_message bytes unpadded:", decompressed_message)

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
