"""Wherever we start execution, 'context.py' sets the Python
search path to start at the project root.  If we start at the project
root, we don't need to adjust the search path, but we need a dummy
context.py so that it can be found by "import context" in other
modules.
"""
pass # Because we're already at project root
