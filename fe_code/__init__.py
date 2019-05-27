"""
Module fe_code
==============
"""

import sys
import numpy

from .structure import Structure
from .kent_park_model import KentParkModel
from .menegotto_pinto_model import MenegottoPintoModel

numpy.set_printoptions(linewidth=1000, floatmode="unique")
if sys.version_info < (3, 6):
    raise RuntimeError("The fiber beam-column module requires at least Python 3.6!")

# MSG = "-------------------------------------------------------\n"
# MSG += "+++++++++ Fiber Beam-Column Program initiated +++++++++\n"
# MSG += "+++++++++++++++++++++++++++++++++++++++++++++++++++++++\n"
# MSG += "\n"
# MSG += "                 Author: Mahmoud Zidan                 \n"
# MSG += "-------------------------------------------------------\n\n"

# MSG = "\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++\n"
# MSG += "+++++++++ Fiber Beam-Column Program initiated +++++++++\n"
# MSG += "+++++++++++++++++++++++++++++++++++++++++++++++++++++++\n\n"

MSG = "  ______ _____ ____  ______ _____\n"
MSG += " |  ____|_   _|  _ \\|  ____|  __ \\ \n"
MSG += " | |__    | | | |_) | |__  | |__) |\n"
MSG += " |  __|   | | |  _ <|  __| |  _  /\n"
MSG += " | |     _| |_| |_) | |____| | \\ \\ \n"
MSG += " |_|__  |_____|____/|______|_|  \\_\\    _____ ____  _     _    _ __  __ _   _ \n"
MSG += " |  _ \\|  ____|   /\\   |  \\/  |       / ____/ __ \\| |   | |  | |  \\/  | \\ | |\n"
MSG += " | |_) | |__     /  \\  | \\  / | ____ | |   | |  | | |   | |  | | \\  / |  \\| |\n"
MSG += " |  _ <|  __|   / /\\ \\ | |\\/| ||____|| |   | |  | | |   | |  | | |\\/| | . ` |\n"
MSG += " | |_) | |____ / ____ \\| |  | |      | |___| |__| | |___| |__| | |  | | |\\  |\n"
MSG += " |____/|______/_/    \\_\\_|  |_|       \\_____\\____/|______\\____/|_|  |_|_| \\_|\n"

print(MSG)
