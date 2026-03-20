from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ModelRef:
    model_id:str
    api_key:str
    base_url:str