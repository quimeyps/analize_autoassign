from pathlib import Path
import ast
import os
from os.path import join

from typing import List

from analyze import (collect_classes_and_autoassign_methods, ClassInfo, FunInfo,
                     collect, guess_package_name)
from pprint import pprint
import pandas as pd
from tqdm import tqdm



if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Inspect a python file for classes that uses the `autoassign` pattern')
    parser.add_argument('python_file', type=Path, nargs='+', help='root folders to search for python source files to inspect')

    args = parser.parse_args()
    root_paths = args.python_file
    if type(root_paths) != list:
        root_paths = [root_paths]

    classes_df = pd.DataFrame(columns=['package', 'folder', 'file', 'class_name', 'is_dataclass', 'is_subclass',
                               'has_init', 'num_methods', 'num_autoassign_methods'])
    functions_df = pd.DataFrame(columns=['package', 'folder', 'file', 'class_name', 'fun_name', 'self_candidate',
                                   'num_ordinary_params', 'num_autoassign_params'])


    for root in root_paths:
        for root, dirs, files in os.walk(root):
            for p in [join(root, name) for name in files]:
                p = Path(p)
                if not p.is_file():
                        continue
                if p.suffix != '.py' or str(p.absolute()).find('__pycache__') != -1:
                    continue
                if p.name.endswith('-info'):
                    continue

                try:
                    with open(p, 'r') as fp:
                        source = fp.read()
                        code_ast = ast.parse(source, filename=p.name)
                        source_lines = source.split('\n')
                except Exception as e:
                    print(f"===== Error of class {e.__class__}")
                    continue

                package = guess_package_name(p)
                folder = str(p.parent)
                file = str(p.name)

                classes, functions = collect_classes_and_autoassign_methods(code_ast)

                new_classes_df, new_functions_df = collect(classes, functions,
                                                   package, folder, file)

                classes_df = pd.concat([classes_df, new_classes_df], sort=False)
                functions_df = pd.concat([functions_df, new_functions_df], sort=False)

    functions_df.to_pickle('methods_data_b.pkl')
    classes_df.to_pickle('classes_data_b.pkl')