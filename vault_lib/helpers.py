import os


def read_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return f.read()
    return None


def read_as_lines(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return f.readlines()
    return []
