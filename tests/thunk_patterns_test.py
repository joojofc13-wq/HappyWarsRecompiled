"""Reject near matches that would change the target or nested this pointer."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_thunk_boundaries import member_virtual_register, constant_tail


class MemberThunkTests(unittest.TestCase):
    words = (0x81630090, 0x386B0084, 0x816B0084, 0x816B0024, 0x7D6903A6, 0x4E800420)

    def test_sibling_argument_entries_share_register_and_destination(self):
        first = bytes.fromhex('38a000004bfff984')
        second = bytes.fromhex('38a000014bfff97c')
        self.assertEqual(constant_tail(first, 0, 0x833C13C0), (5, 0x833C0D48))
        self.assertEqual(constant_tail(second, 0, 0x833C13C8), (5, 0x833C0D48))
        self.assertIsNone(constant_tail(bytes.fromhex('38a000014bfff97d'), 0, 0x833C13C8))

    def test_original_difficulty_adapter(self):
        self.assertEqual(member_virtual_register(struct.pack('>6I', *self.words), 0), 11)

    def test_mismatched_member_register_target_or_link_is_rejected(self):
        for index, replacement in ((1, 0x386A0084), (2, 0x816B0088),
                                   (3, 0x818B0024), (4, 0x7D8903A6), (5, 0x4E800421)):
            words = list(self.words)
            words[index] = replacement
            self.assertIsNone(member_virtual_register(struct.pack('>6I', *words), 0))
        self.assertIsNone(member_virtual_register(b'\0'*20, 0))


if __name__ == '__main__':
    unittest.main()
