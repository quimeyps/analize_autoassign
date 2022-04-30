import ast
import pathlib
from typing import List, Tuple, Optional
from collections import namedtuple
import pandas as pd

ClassInfo = namedtuple('ClassInfo', [ 'class_name', 'class_node', 'is_dataclass', 'is_subclass', 'has_init',
                                     'num_methods', 'autoassign_methods', 'num_autoassign_methods'])

FunInfo = namedtuple('FunInfo', [ 'class_name', 'fun_name', 'fun_node', 'self_candidate',
                                 'autoassign_params', 'ordinary_params'])


def number_of_parameters(fundef_node: ast.FunctionDef):
    """returns the number of *named* parameters, i.e., omits
        *kargs and **kwargs for the `fundef_node` FunctionDef AST"""
    arguments = fundef_node.args
    def len_zero_if_none(list_or_none):
        len(list_or_none) if list_or_none is not None else 0

    return len_zero_if_none(arguments.posonlyargs) + \
            len_zero_if_none(arguments.args) + \
            len_zero_if_none(arguments.kwonlyargs)


def split_self_candidate(fundef_node: ast.FunctionDef):
    """splits the total list of named parameters in returning the 2-tuple
     (`self_candidate`, `other_parameters`). If there isn't a suitable
     `self_candidate`, that is the first not kwonlyarg, returns None in the
     first position.
     """
    arguments = fundef_node.args

    other_parameters = []  # includes all arguments but the first
    if (arguments.posonlyargs is not None) and (len(arguments.posonlyargs) > 0):
        self_candidate = arguments.posonlyargs[0]
        other_parameters.extend(arguments.posonlyargs[1:])
        if arguments.args is not None:
            other_parameters.extend(arguments.args)
    elif (arguments.args is not None) and (len(arguments.args) > 0):
        self_candidate = arguments.args[0]
        other_parameters.extend(arguments.args[1:])
    else:
        # self can't be a kwonlyarg
        return None, arguments.kwonlyargs

    if arguments.kwonlyargs is not None:
        other_parameters.extend(arguments.kwonlyargs)
    return self_candidate, other_parameters


def is_autoassign(node: ast.Assign, self_id: str, attr_id: str):
    """returns True if the Assign `node` follows the pattern
      `self_id.attr_id = attr_id`"""
    if len(node.targets) == 0: return False
    if len(node.targets) > 1: return False

    target = node.targets[0]
    if not isinstance(target, ast.Attribute): return False
    if not isinstance(target.value, ast.Name): return False
    if not isinstance(target.value.ctx, ast.Load): return False
    if not isinstance(target.value.ctx, ast.Load): return False
    if not isinstance(target.ctx, ast.Store): return False
    if target.value.id != self_id: return False

    attr_name = target.attr
    rhs = node.value
    if not isinstance(rhs, ast.Name): return False
    if not isinstance(rhs.ctx, ast.Load): return False
    rhs_name = rhs.id

    if (rhs_name == attr_name) and (attr_name == attr_id):
        return True


def classify_parameters(fundef_node: ast.FunctionDef) -> Tuple[Optional[ast.arg], List[ast.arg], List[Tuple[ast.arg, ast.Assign]]]:
    """classify parameters as `self_candidate`, `autoassign_parameter`
    or `regular_parameter`

    Returns a 3-tuple: (self_candidate, regular_parameter, autoassign_parameter),
    """
    self_candidate, other_parameters = split_self_candidate(fundef_node)
    if self_candidate is None:
        return None, [], other_parameters

    self_name = self_candidate.arg
    autoassign_nodes = []
    ordinary_parameters = []

    assign_nodes = [node for node in fundef_node.body if isinstance(node, ast.Assign)]
    for auto_arg in other_parameters:
        autoassign_for_arg = [assign for assign in assign_nodes if is_autoassign(assign, self_name, auto_arg.arg)]
        if len(autoassign_for_arg)>0:
            autoassign_nodes.append((auto_arg, autoassign_for_arg[0]))
        else:
            ordinary_parameters.append(auto_arg)
    return self_candidate, ordinary_parameters, autoassign_nodes


def is_dataclass(node: ast.ClassDef):
    if node.decorator_list is None: return False

    for dec in node.decorator_list:
        if isinstance(dec, ast.Name) and dec.id == 'dataclass':
            return True
        elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id == 'dataclass':
            return True
    return False


def get_dataclass_decorator(node: ast.ClassDef):
    """returns the node representing the dataclass decorator or None
    if the class doen't have this decorator"""
    if node.decorator_list is None: return None

    for dec in node.decorator_list:
        if isinstance(dec, ast.Name) and dec.id == 'dataclass':
            return dec
        elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id == 'dataclass':
            return dec
    return None


def collect_classes_and_autoassign_methods(code_ast: ast.AST):
    """search for classes in the first level of the AST and collects useful information
    to asses whether the automatic autoassign syntax could be useful.

     Mainly, it collects the methods that implement the pattern `self.something = something`
     (`autoassign_methods`), but also register if the class in question is a dataclass, if it
     is a subclass, if defines an `__init__`, how many total methods define (it doesn't check
     if some of them are static or classmethods, yet).

    """
    classes = []
    autoassign_methods = []
    classes_in_ast = [node for node in code_ast.body if isinstance(node, ast.ClassDef)]
    for n, class_node in enumerate(classes_in_ast):
        class_name = class_node.name
        num_autoassign_methods = 0

        dataclass_decorator = get_dataclass_decorator(class_node)
        is_dataclass = (dataclass_decorator is not None)
        has_init = False
        is_subclass = ((class_node.bases is not None) and len(class_node.bases) > 0)


        fundef_child_nodes = [child_node for child_node in class_node.body
                              if isinstance(child_node, ast.FunctionDef)]
        has_init = '__init__' in [fun.name for fun in fundef_child_nodes]
        num_methods = len(fundef_child_nodes)

        autoassign_methods = []
        for fundef in fundef_child_nodes:
            self_candidate, other_parameters, autoassign_parameters = classify_parameters(fundef)
            num_autoassign_methods += 1 if len(autoassign_parameters) > 0 else 0
            if len(autoassign_parameters) > 0:
                autoassign_methods.append(FunInfo(class_name=class_name, fun_name=fundef.name, fun_node=fundef,
                                                  self_candidate=self_candidate if self_candidate else '',
                                                  ordinary_params=other_parameters,
                                                  autoassign_params=autoassign_parameters))

        classes.append(ClassInfo(class_name=class_name, class_node=class_node, is_dataclass=is_dataclass,
                                 is_subclass=is_subclass, has_init=has_init, autoassign_methods=autoassign_methods,
                                 num_methods=len(fundef_child_nodes), num_autoassign_methods=len(autoassign_methods)))

    return classes, autoassign_methods

def collect(classes: List[ClassInfo], functions: List[FunInfo], package: str,
            folder: str, file: str):
    classes_df = pd.DataFrame(columns=['package', 'folder', 'file', 'class_name', 'is_dataclass', 'is_subclass',
                               'has_init', 'num_ordinary_methods', 'num_autoassign_methods'])
    fun_df = pd.DataFrame(columns=['package', 'folder', 'file', 'class_name', 'fun_name', 'self_candidate',
                                   'num_ordinary_params', 'num_autoassign_params'])

    for class_item in classes:
        classes_df.loc[len(classes_df.index)] = \
            {'package': package, 'folder': folder, 'file': file,
            'class_name': class_item.class_name, 'is_dataclass': class_item.is_dataclass,
            'is_subclass': class_item.is_subclass, 'has_init': class_item.has_init,
             'num_ordinary_methods': class_item.num_methods-class_item.num_autoassign_methods,
            'num_autoassign_methods': class_item.num_autoassign_methods}

    for fun_item in functions:
        fun_df.loc[len(fun_df.index)] = \
            {'package': package, 'folder': folder, 'file': file,
            'class_name': fun_item.class_name, 'fun_name': fun_item.fun_name,
             'self_candidate': fun_item.self_candidate.arg,
             'num_ordinary_params': len(fun_item.ordinary_params),
             'num_autoassign_params': len(fun_item.autoassign_params)}

    return classes_df, fun_df

def guess_package_name(input_file: pathlib.Path):
    path_parts = input_file.parts
    try:
        # search 'site-packages'
        package = path_parts[path_parts.index('site-packages') + 1]
        return package
    except ValueError:
        pass
    try:
        # search 'site-packages'
        package = path_parts[path_parts.index('Lib') + 1]
        return 'stdlib'
    except ValueError:
        pass

    return 'unknown'

