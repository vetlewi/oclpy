
import numpy as np
import pandas as pd
import oclpy as ocl
import os
import pathlib
import unittest

mypath = pathlib.Path()

class TestCurveCalibrate(unittest.TestCase):

    def test_read(self):
        path = str(mypath)
        path = path + "/test_data/curves/"
        result = ocl.GetCurves(names=['proton_r%d.txt', 'deutron_r%d.txt', 'triton_r%d.txt'],
                               base=path,
                               index=range(16))

        self.assertIsInstance(result, dict)
        kinds = []
        for key in result.keys():
            k, r = key
            kinds.append(k)

        self.assertIn('p', kinds)
        self.assertIn('d', kinds)
        self.assertIn('t', kinds)




if __name__ == "__main__":
    mypath = pathlib.Path(os.path.realpath(__file__))
    mypath = mypath.parent
    unittest.main()
