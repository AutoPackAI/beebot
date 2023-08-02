from dataclasses import dataclass


@dataclass
class Observation:
    response: any = ""
    error_reason: str = ""
    success: bool = True
