from expression import Secret
from test_integration import suite


def main():

    """
        f(a, b) = a - b
        """
    alice_secret = Secret()
    bob_secret = Secret()

    parties = {
        "Alice": {alice_secret: 14},
        "Bob": {bob_secret: 3},
    }

    expr = (alice_secret - bob_secret)
    expected = 14 - 3
    suite(parties, expr, expected)


if __name__ == '__main__':
    main()