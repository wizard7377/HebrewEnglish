
import csv
from pathlib import Path

from pydantic import FilePath

import torch as torch


CWD = Path(__file__).parent
DATA = list(csv.DictReader(open(CWD / "morph.csv", "r")))

PARTS_OF_SPEECH = list(set({row["pos"] for row in DATA}))
STEMS = list(set({row["stem"] for row in DATA}))
TYPES = list(set({row["type"] for row in DATA}))
PERSONS = list(set({row["person"] for row in DATA}))
NUMBERS = list(set({row["number"] for row in DATA}))
GENDERS = list(set({row["gender"] for row in DATA}))
STATES = list(set({row["state"] for row in DATA}))
TOTAL = sum([int(row["count"]) for row in DATA])

def data_to_tensor(data: dict) -> torch.