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
There are two binaries, one to inspect a single file, and get a printed report on stdout of the detected 
functions, and the other traverse directories with installed python packages (site-package or other user selected directories),
and collect the information 

## Caveats:
- Only consider classes at the top of the file (nested classes are not considered.
- Only functions defined inside a top class are considered, irrespective of the decorators 
that they may have. In other words, a static method is analized the same as an instance method.
- This code doesn't check that the parameter is not manipulated before being assigned. For example:
```python
class A:
  def __init__(self, names):
    names = ','.split(names)
    self.names = names
```
would result in a false positive. This function is not suitable to be used with the proposed autoassign syntax, 
but it would be counted as if it were.
