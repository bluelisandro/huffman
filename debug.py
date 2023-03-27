import os
import sys
from typing import Dict
import heapq

# 1. Create frequency tree for each byte
# 2. Create minheap with smallest frequency as root

def frequencyTree(message: bytes) -> Dict:
    """ Given the bytes read from a file, returns a dictionary containing the frequency of each byte in the file.

    :param message: raw sequence of bytes from a file
    :returns: dict containing the frequency of each byte in the file
    """
    # freq = {}
    # for byte in message:
    #     freq[byte] = freq.get(byte, 0) + 1
    # return freq
    return {byte: message.count(byte) for byte in set(message)}

def minHeap(freq: Dict) -> list:
    """ Given a dictionary containing the frequency of each byte in a file, returns a minheap containing the frequency tree for each byte.

    :param freq: dict containing the frequency of each byte in a file
    :returns: minheap containing the frequency tree for each byte
    """
    return heapq.heapify([(v, k) for k, v in freq.items()])


if __name__ == '__main__':
    infile = sys.argv[1]
    if not os.path.exists(infile):
        raise FileExistsError(f'{infile} does not exist.')

    with open(infile, 'rb') as fp:
        message = fp.read()
        freq = frequencyTree(message)
        print("Freuency Tree:")
        for k, v in freq.items():
            print(chr(k), v)
        minheap = minHeap(freq)
        print("Minheap:")
