"""
This module contains the ColorPrinter class, which is a callable object that
prints text in a specified color.
"""
import colorama

colorama.just_fix_windows_console()

COLORS = {
    "BLACK": colorama.Fore.BLACK,
    "RED": colorama.Fore.RED,
    "GREEN": colorama.Fore.GREEN,
    "YELLOW": colorama.Fore.YELLOW,
    "BLUE": colorama.Fore.BLUE,
    "MAGENTA": colorama.Fore.MAGENTA,
    "CYAN": colorama.Fore.CYAN,
    "WHITE": colorama.Fore.WHITE,
    "RESET": colorama.Fore.RESET,
    "LIGHTBLACK_EX": colorama.Fore.LIGHTBLACK_EX,
    "LIGHTRED_EX": colorama.Fore.LIGHTRED_EX,
    "LIGHTGREEN_EX": colorama.Fore.LIGHTGREEN_EX,
    "LIGHTYELLOW_EX": colorama.Fore.LIGHTYELLOW_EX,
    "LIGHTBLUE_EX": colorama.Fore.LIGHTBLUE_EX,
    "LIGHTMAGENTA_EX": colorama.Fore.LIGHTMAGENTA_EX,
    "LIGHTCYAN_EX": colorama.Fore.LIGHTCYAN_EX,
    "LIGHTWHITE_EX": colorama.Fore.LIGHTWHITE_EX,
}


class ColorPrinter:
    def __init__(
        self,
        color: str,
    ) -> None:
        self.color = COLORS[color]

    def __call__(self, *args, **kwargs) -> None:
        print(f"{self.color}", end="")
        print(*args, **kwargs)
        print(f"{colorama.Style.RESET_ALL}", end="", flush=True)
