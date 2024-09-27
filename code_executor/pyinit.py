import numpy as np
import pandas as pd
import dill
import matplotlib.pyplot as plt

def save_object(filename):
    variables = globals().copy()
    filtered_variables = {name: value for name, value in variables.items() if not name.startswith('__')}
    with open(filename, 'wb') as f:
        dill.dump(filtered_variables, f)

def load_object(filename):
    with open(filename, "rb") as f:
        vars = dill.load(f)
        globals().update(vars)
