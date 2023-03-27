from huffman import encode
import unittest
from typing import Tuple, Dict

# Test class
class TestHuffmanEncoding(unittest.TestCase):
    def test_encode(self):
        # Test input (message as bytes)
        message = b"Hello, I am DeveloperGPT!"
        # Call the encode function
        encoded_message, decoder_ring = encode(message)
        # Check if the output is in the expected format (i.e., string and dict)
        self.assertIsInstance(encoded_message, str)
        self.assertIsInstance(decoder_ring, dict)
        # Add more assertions to check if the encoded_message and decoder_ring
        # are correct according to your implementation

if __name__ == "__main__":
    unittest.main()
