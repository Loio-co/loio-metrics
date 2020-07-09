from .span import Span
from .lft_utils import construct_ltf
from .metrics_utils import calc_counters_with_partial

__version__: str = "0.0.1"


def version():
    return __version__
