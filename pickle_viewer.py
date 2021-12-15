import pickle
import pandas as pd
import numpy as np
from pprint import pprint
import argparse

parser = argparse.ArgumentParser(description="...")
parser.add_argument('file', metavar = 'file', type = str)

args = parser.parse_args()

data = pickle.load(open(args.file, 'rb'))

pprint(data)