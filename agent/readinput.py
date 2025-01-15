"""
This module provides functionality for reading multiple lines from user input.
"""


def read_lines() -> str:
    """
    Reads lines from the user until "END" or EOF is encountered.
    """
    lines = ""
    try:
        while True:
            line = input()
            if line == "END":
                break
            lines += line
            lines += "\n"
    except EOFError:
        pass
    return lines
