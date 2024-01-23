"""Test a translator (file-to-file transformation)
across a set of source and expected product files.

"""
import subprocess
import pathlib
import argparse
import subprocess

# The filter we will be testing
COMMAND = "python3 compiler/compile.py "

def cli() -> object:
    """Command line interface"""
    parser = argparse.ArgumentParser("Check expected output of translators")
    parser.add_argument("sources",
                        help="Directory of source files to translate",
                        type=str)
    parser.add_argument("expectations",
                        help="Directory of expected outputs",
                        type=str)
    