# analize_autoassign
Code to analize python source files to asses if it could benefit for the autoassign syntax proposed 
in this [thread](https://mail.python.org/archives/list/python-ideas@python.org/thread/SCXHEWCHBJN3A7DPGGPPFLSTMBLLAOTX/) of the python-ideas mailing list.

Currently, this code allows to search for functions defined inside classes that follow this pattern:
```python

class A:
  ...
  def some_method(s, t, v, w):
    ...
    s.t = t
    s.v = v
  ...
```
In this example, `some_method` is considered a function that follows the autoassign pattern, `s` is considered 
the "self candidate", and of the three remaining parameters, only `t` and `v` could be autoassigned.

## Usage:
There are two binaries, one to inspect a single file (`inspect_file.py`), and get a printed report on stdout of the detected 
functions, and the other (`inspect_library.py`) traverse directories with installed python packages (site-package or other user selected directories),
and collect the information in two pandas DataFrame (one for classes and the other for methods):
- `python inspect_file.py <filename>`
  + output to stdout
- `python inspect_library.py <folder1> <folder2> ... <folderN>`
  + output two files: `classes_data_b.pkl` and `methods_data_b.pkl` (the names are hardcoded for now).
  + In methods dataframe, there are only entries for autoassign methods candidates, with some information regarding the number
    of parameters that could be autoassigned, and the number of parameters that can't be autoassigned.
  + In the classes dataframe there is information of **all** the classes, indicating the package, the file, if has a dataclass decorator, if it is a subclass, te numebr of methods that defined (again, could include static methods and others), and the numebr of methods that follow the autoassign pattern. 

There is also a jupyter python notebook (`explore_stats.ipynb`), that it doesn't have that much code. It simply loads the pandas pickles, and perform 
some simple statistic. The printed messages in the notebook are currently in spanish. 

There are an example output 


## Caveats:
- Only consider classes at the top of the file (nested classes are not considered.
- Only functions defined inside a top class are considered, irrespective of the decorators 
that they may have. In other words, a static method is analized the same as an instance method.
- This code doesn't check that the parameter is not manipulated before being assigned. For example:
```python
class A:
  def __init__(self, names):
    names = names.split(',')
    self.names = names
```
would result in a false positive. This function is not suitable to be used with the proposed autoassign syntax, 
but it would be counted as if it were.
