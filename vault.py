#!/usr/bin/env python3
# Super Beta
import argparse
import os.path
from secure_web3 import sw3_wallet, sw3


class Vault:
    def __init__(self, wallet_file: str, network: str = 'ethereum', init=False):
        self.wallet_file = wallet_file
        self.sw3 = sw3.SecureWeb3(wallet_file, network)
        if not self.check_wallet():
            return
        self.sw3.load_wallet()
        self.sw3.setup_w3()
        self.sw3_wallet = sw3_wallet.EtherShellWallet(self.sw3)

    def check_wallet(self, init=False):
        if init:
            return self.configure_wallet()
        if not os.path.exists(self.wallet_file):
            print(f'[!] Wallet does not exist: {self.wallet_file}')
            return False
            # exit()
        return True

    def configure_wallet(self):
        print('Configuring .. ')
        self.sw3.configure_wallet()

    def check_w3_chain_id(self):
        if self.sw3.w3.isConnected():
            cid = self.sw3.w3.eth.chain_id
            return cid
        return False


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('-w', '--wallet', type=str, default='keys/default_wallet.json')
    args.add_argument('-i', '--init', action='store_true', help='Import private key and initialize the wallet.')
    args = args.parse_args()
    vault = Vault('keys/default_wallet.json')
    print('[!] Warning: this is really alpha!')

    if args.init:
        vault.configure_wallet()
    cid = vault.check_w3_chain_id()
    if cid:
        print(f'[+] Web3 is connected to {cid}.')
    else:
        print('[-] Web3 is not connected.')
