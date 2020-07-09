from dataclasses import dataclass


@dataclass
class Span:
    start: int = 0
    finish: int = 0
