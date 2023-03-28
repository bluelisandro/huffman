import os
import sys
from typing import Dict, Tuple
import heapq

# 1. Create frequency tree for each byte
# 2. Create minheap with smallest frequency as root,
# this is to sort the freuencies from least to greatest


def freq_tree(message: bytes) -> Dict:
    """ Given the bytes read from a file, returns a dictionary containing the frequency of each byte in the file.

    :param message: raw sequence of bytes from a file
    :returns: dict containing the frequency of each byte in the file
    """
    # freq = {}
    # for byte in message:
    #     freq[byte] = freq.get(byte, 0) + 1
    # return freq
    return {byte: message.count(byte) for byte in set(message)}


def create_freq_min_heap(freq: Dict) -> list:
    """ Given a dictionary containing the frequency of each byte in a file, returns a minheap containing the frequency tree for each byte.

    :param freq: dict containing the frequency of each byte in a file
    :returns: minheap containing the frequency tree for each byte
    """
    # return heapq.heapify([(v, k) for k, v in freq.items()])
    freq_min_heap = []
    for k, v in freq.items():
        heapq.heappush(freq_min_heap, (v, k))
    return freq_min_heap


def huffman_tree(freq_min_heap: list) -> list:
    """ Given a minheap containing the frequency tree for each byte, returns a huffman tree.

    :param minheap: minheap containing the frequency tree for each byte
    :returns: huffman tree
    """
    # 1. Pop the two smallest frequencies from the minheap
    # 2. Create a new node with the sum of the two frequencies as the frequency
    # 3. Add the two smallest frequencies as children to the new node,
    #    the smallest frequency is the left child, the second smallest is the right child
    # 4. Add the new node to the minheap
    # 5. Repeat steps 1-4 until there is only one node left in the minheap

    # huffman_min_heap = []
    # print("\n")
    while len(freq_min_heap) > 1:
        left = heapq.heappop(freq_min_heap)
        right = heapq.heappop(freq_min_heap)
        # print("Pop:", left, right)
        new = (left[0] + right[0], left, right)
        heapq.heappush(freq_min_heap, new)

    return freq_min_heap[0]


def encoder_ring(huffman_tree: list):
    """
    Steps to print codes from Huffman Tree:
    1. Traverse the tree formed starting from the root.
    2. Maintain an auxiliary array.
    3. While moving to the left child, write 0 to the array.
    4. While moving to the right child, write 1 to the array.
    5. Print the array when a leaf node is encountered
    """
    codes = {}
    # Tuple[frequency, left, right]

    def _encoder_ring(node: Tuple[int, any, any], code: str):
        # If a node has only one child, its left child is a leaf node
        # so we can add the code to the dictionary
        if len(node) == 2:
            codes[node[1]] = code
        else:
            _encoder_ring(node[1], code + '0')
            _encoder_ring(node[2], code + '1')
    _encoder_ring(huffman_tree, '')
    return codes


def encode(message: bytes, codes: Dict) -> bytes:
    """
    Given a message and a dictionary containing the encoding ring,
    returns the encoded message.
    """
    encoded_bytes = ""
    for byte in message:
        encoded_bytes += codes[byte]

    return encoded_bytes


def decode(encoded_bytes: bytes, codes: Dict) -> bytes:
    """
    Given an encoded message and a dictionary containing the encoding ring,
    returns the decoded message.
    """
    decoded_message = []
    encoded_str = str(encoded_bytes)
    buffer = ''
    flipped_codes = {v: k for k, v in codes.items()}

    for bit in encoded_str:
        print(bit)
        buffer += bit
        if buffer in flipped_codes:
            decoded_message.append(flipped_codes[buffer])
            buffer = ''

    return decoded_message


if __name__ == '__main__':
    infile = sys.argv[1]
    if not os.path.exists(infile):
        raise FileExistsError(f'{infile} does not exist.')

    with open(infile, 'rb') as fp:
        message = fp.read()

        freq = freq_tree(message)
        print("Freq Tree:")
        # [print(chr(k), v) for k, v in freq.items()]
        print(freq)

        freq_min_heap = create_freq_min_heap(freq)
        print("\nFreq Minheap:")
        print(freq_min_heap)

        huffman_min_heap = huffman_tree(freq_min_heap)
        print("\nHuffman Tree:")
        print(huffman_min_heap)

        codes = encoder_ring(huffman_min_heap)
        print("\nEncoding ring:")
        print(codes)

        encoded_bytes = encode(message, codes)
        print("\nEncoded bytes:")
        print(encoded_bytes)

        decoded_bytes = decode(encoded_bytes, codes)
        print("\nDecoded bytes:")
        print(decoded_bytes)
        for byte in decoded_bytes:
            print(chr(byte), end='')
        # print=[chr(byte) for byte in decoded_bytes]


"""
            (40, 
        (18, 
    (8, 'C'),       (10, 
            (4, 'G'), (6, 'A'))), 
                                    (22, 'T'))

Steps to print codes from Huffman Tree:
    Traverse the tree formed starting from the root. 
    Maintain an auxiliary array. 
    While moving to the left child, write 0 to the array.
    While moving to the right child, write 1 to the array. 
    Print the array when a leaf node is encountered
"""
