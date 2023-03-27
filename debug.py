import os
import sys
from typing import Dict
from collections import defaultdict
import heapq

# 1. Create frequency tree for each byte
# 2. Create minheap with smallest frequency as root

def frequencyTree(message: bytes) -> Dict:
    """ Given the bytes read from a file, returns a dictionary containing the frequency of each byte in the file.

    :param message: raw sequence of bytes from a file
    :returns: dict containing the frequency of each byte in the file
    """
    freq = defaultdict(int)
    for byte in message:
        freq[byte] += 1

    return freq


if __name__ == '__main__':
    infile = sys.argv[1]
    if not os.path.exists(infile):
        raise FileExistsError(f'{infile} does not exist.')

    with open(infile, 'rb') as fp:
        message = fp.read()
        freq = frequencyTree(message)
        for k, v in freq.items():
            print(chr(k), v)