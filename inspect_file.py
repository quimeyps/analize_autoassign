from pathlib import Path
import ast

from typing import List

from analyze import (collect_classes_and_autoassign_methods, ClassInfo, FunInfo,
                     collect, guess_package_name)
from report import report
from pprint import pprint
import pandas as pd
from tqdm import tqdm


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Inspect a python file for classes that uses the `autoassign` pattern')
    parser.add_argument('python_file', type=Path, help='python source file to inspect')

    args = parser.parse_args()
    input_file = args.python_file


    package = guess_package_name(input_file)
    folder = str(input_file.parent)
    file = str(input_file.name)

    with open(input_file, 'r') as fp:
        source = fp.read()
        code_ast = ast.parse(source, filename=input_file.name)
        source_lines = source.split('\n')

    classes, functions = collect_classes_and_autoassign_methods(code_ast)
    report(classes, source_lines)

    classes_df, functions_df = collect(classes, functions,
                                       package, folder, file)

    print()
    print()
    print(classes_df)
    print()
    print()
    print(functions_df)