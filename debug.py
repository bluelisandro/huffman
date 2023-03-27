import os
import sys
from typing import Dict
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
        heapq.heappush(freq_min_heap, (v, chr(k)))
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
    while len(freq_min_heap) > 1:
        left = heapq.heappop(freq_min_heap)
        right = heapq.heappop(freq_min_heap)
        new = (left[0] + right[0], left, right)
        heapq.heappush(freq_min_heap, new)

    return freq_min_heap


if __name__ == '__main__':
    infile = sys.argv[1]
    if not os.path.exists(infile):
        raise FileExistsError(f'{infile} does not exist.')

    with open(infile, 'rb') as fp:
        message = fp.read()
        freq = freq_tree(message)
        print("Freq Tree:")
        for k, v in freq.items():
            print(chr(k), v)
        freq_min_heap = create_freq_min_heap(freq)
        print("\nFreq Minheap:")
        print(freq_min_heap)
        huffman_min_heap = huffman_tree(freq_min_heap)
        print("\nHuffman Tree:")
        print(huffman_min_heap) 
