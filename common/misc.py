""" a collection of miscellaneous utilities """

from colorama import Fore, Style
from pandas import DataFrame

colours = {
    "red": Fore.RED,
    "cyan": Fore.CYAN,
    "magenta": Fore.MAGENTA,
    "yellow": Fore.YELLOW,
    "green": Fore.LIGHTGREEN_EX,
    "default": Fore.RESET,
}


def cprint(colour, *obj):
    if colour in list(colours.keys()):
        print(colours[colour] + " ".join([str(i) for i in obj]) + Style.RESET_ALL)
    else:
        print(colours["default"] + " ".join([str(i) for i in obj]) + Style.RESET_ALL)
