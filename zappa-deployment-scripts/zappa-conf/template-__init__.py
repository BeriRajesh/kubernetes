from __future__ import print_function
import os
import sys

if os.path.dirname(__file__) != "":
    sys.path.insert(0, os.path.dirname(__file__))
    print("Added to PATH: " + os.path.dirname(__file__))
