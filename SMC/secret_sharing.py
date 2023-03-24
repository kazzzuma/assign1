"""
Secret sharing scheme.
"""

from __future__ import annotations

import random
from typing import List


class Share:
    """
    A secret share in a finite field.
    """
    FIELD_P = 3525679

    def __init__(self, value, *args, **kwargs):
        # Adapt constructor arguments as you wish
        self.value = value % self.FIELD_P

    def __repr__(self):
        # Helps with debugging.
        raise NotImplementedError("You need to implement this method.")

    def __add__(self, other):
        return Share((self.value + other.value) % self.FIELD_P)

    def __sub__(self, other):
        return Share((self.value - other.value) % self.FIELD_P)

    def __mul__(self, other):
        raise NotImplementedError("You need to implement this method.")

    def serialize(self):
        """Generate a representation suitable for passing in a message."""
        raise NotImplementedError("You need to implement this method.")

    @staticmethod
    def deserialize(serialized) -> Share:
        """Restore object from its serialized representation."""
        raise NotImplementedError("You need to implement this method.")


def share_secret(secret: int, num_shares: int) -> List[Share]:
    """Generate secret shares."""
    F_P = Share.FIELD_P
    shares_value = random.sample(range(0, F_P), num_shares - 1)
    share_0 = secret - sum(shares_value)
    share_value_list = [share_0] + shares_value

    return [Share(val) for val in share_value_list]


def reconstruct_secret(shares: List[Share]) -> int:
    """Reconstruct the secret from shares."""
    return sum(shares, start=Share(0)).value % Share.FIELD_P


# Feel free to add as many methods as you want.
