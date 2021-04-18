import numpy as np
import pytest

def compare_mv_num_dict(d1, d2):
    assert d1['i'] == d2['i'], "The numeric model vars 'i' does not match!"
    assert d1['h'] == d2['h'], "The numeric model vars 'h' does not match!"
    assert np.all(d1['o'][0] == d2['o'][0]), "The numeric model vars 'o'[0] does not match!"
    assert np.all(d1['o'][1] == d2['o'][1]), "The numeric model vars 'o'[1] does not match!"
    assert np.all(d1['d'][0] == d2['d'][0]), "The numeric model vars 'd'[0] does not match!"
    assert np.all(d1['d'][1] == d2['d'][1]), "The numeric model vars 'd'[1] does not match!"