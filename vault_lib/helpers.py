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


def parse_tx_ret_val(ret):
    if ret:
        print(f'[+] TXID: {ret}')
    else:
        print('[!] Transaction failed to broadcast.')
