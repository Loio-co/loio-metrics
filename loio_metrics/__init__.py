from .span import Span
from .lft_utils import construct_ltf, parse_ltf
from .metrics_utils import calc_counters_with_partial, sort_and_glue_overlapped

__version__: str = "0.0.2"


def version():
    return __version__
