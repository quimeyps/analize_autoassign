from analyze import ClassInfo, FunInfo
from typing import List, Tuple, Optional


def print_class_info(class_item: ClassInfo, source_lines: List[str]):
    class_node = class_item.class_node
    if class_item.is_dataclass:
        print(f'{numbered_line(class_node.lineno - 1)}')
    print(f'{numbered_line(class_node.lineno, source_lines)}')
    print_class_info_comment(class_item)


def print_class_info_comment(class_item: ClassInfo):
    print(f"""
# - {'Is subclass' if class_item.is_subclass else 'It isn''t subclass'}
# - {'Is dataclass' if class_item.is_dataclass else 'It isn''t dataclass'}
# - {'Has init' if class_item.has_init else 'Doesn''t has init'}
# - Num methods: {class_item.num_methods}
# - Num autoassign_methods: {class_item.num_autoassign_methods}
        """)


def print_autoassign_method_info(fun_item: FunInfo, source_lines: List[str]):
    argument_lines = list(set([fun_item.fun_node.lineno, fun_item.self_candidate.lineno] +
                              [param.lineno for param in fun_item.ordinary_params] + \
                              [param.lineno for param, _ in fun_item.autoassign_params]))
    argument_lines.sort()
    print('\n'.join([numbered_line(lineno, source_lines) for lineno in argument_lines]))
    print_method_info_comment(fun_item)
    for _, auto_assign in  fun_item.autoassign_params:
        print(numbered_line(auto_assign.lineno, source_lines))




def print_method_info_comment(fun_item: FunInfo):
    print(f"""
    # - self_candidate_name: {fun_item.self_candidate.arg}  
    # - Num ordinary params: {len(fun_item.ordinary_params)}
    # - Num autoassign params: {len(fun_item.autoassign_params)}
    """)


def numbered_line(lineno: int, source_lines: List[str]):
    return f'{lineno:3d}    {source_lines[lineno - 1]}'


def report(classes: List[ClassInfo], source_lines: List[str],
           show_autoassign=True, show_dataclasses=False, show_issubclass=False):

    for class_item in classes:
        if class_item.num_autoassign_methods>0 and show_autoassign:
            print_class_info(class_item, source_lines)
            for fun in class_item.autoassign_methods:
                print_autoassign_method_info(fun, source_lines)

        elif class_item.is_dataclass and show_dataclasses:
            print_class_info(class_item, source_lines)
        elif class_item.is_dataclass and show_issubclass:
            print_class_info(class_item, source_lines)
