#!/usr/bin/env python3
# Super Beta
import argparse
import os.path

from eth_typing import ChecksumAddress
from secure_web3 import sw3_wallet, sw3
from ethervault.vault_lib import exceptions

import secure_web3.sw3_wallet


class VaultCli:
    def __init__(self, wallet_file: str, network: str = 'ethereum', init: bool = False):
        """
        Command Line Ethervault controller tool
        (note: see docs)

        Tool for deploying, depositing, administering the contract.
        :param wallet_file: json wallet file
        :param network: ie "ethereum"
        :param init: import private key and setup wallet
        """
        self.wallet_file = wallet_file
        self.sw3 = sw3.SecureWeb3(wallet_file, network)
        self._w3 = sw3.SecureWeb3.w3

        if not self.check_wallet(init):
            return
        self.sw3.load_wallet()
        self.sw3.setup_w3()
        self.sw3_wallet = sw3_wallet.EtherShellWallet(self.sw3)

    def check_wallet(self, init=False):
        """

        :param init:
        :return: bool
        """
        if init:
            return self.configure_wallet()
        if not os.path.exists(self.wallet_file):
            print(f'[!] Wallet does not exist: {self.wallet_file}')
            return False
            # exit()
        return True

    def configure_wallet(self) -> bool:
        """

        :return:
        """
        print('Configuring .. ')
        if self.sw3.configure_wallet():
            return True
        return False

    def check_w3_chain_id(self) -> int:
        """
        Return the chain ID
        :return: int
        """
        if self.sw3.w3.isConnected():
            cid = self.sw3.w3.eth.chain_id
            return cid
        return False

    def _contract(self):
        if hasattr(self, 'contract'):
            return self.contract
        raise exceptions.ContractNotConfigured('Please specify your contract address on '
                                               'this network in your wallet file.')

    def deposit_ether(self, qty: float) -> (hex, bool):
        """
        Deposit in contract
        :param qty:
        :return: hex(txid)
        """
        # TODO: implement these functions
        pass

    def propose_withdrawal(self, destination: ChecksumAddress, quantity: float):
        pass

    def revoke_withdrawal(self, transaction_id: int):
        pass

    def confirm_withdrawal(self):
        pass

    def initiate_proposal(self, signer_address: ChecksumAddress, limit: float, threshold: int):
        pass

    def approve_proposal(self, proposal_id):
        pass

    def revoke_proposal(self, proposal_id):
        pass


def vault_cli():
    args = argparse.ArgumentParser()
    args.add_argument('-w', '--wallet', type=str, default='keys/default_wallet.json')
    args.add_argument('-i', '--init', action='store_true', help='Import private key and initialize the wallet.')
    args.add_argument('-n', '--network', type=str, default='goerli', help='The EVM chain to operate on.')
    subparsers = args.add_subparsers(dest='command')
    deposit = subparsers.add_parser('deposit', help='Deposit ether')
    deposit.add_argument(
        '--dry-run',
        help='do not deposit, just pretend',
        action='store_true'
    )
    deposit.add_argument('-q', '--quantity', nargs=1, type=float, help='Ether amount')

    args = args.parse_args()
    vault = VaultCli('keys/default_wallet.json')
    print('[!] Warning: this is really alpha and not everything is implemented yet.')

    if args.init:
        vault.configure_wallet()
    cid = vault.check_w3_chain_id()
    if cid:
        print(f'[+] Web3 is connected to {cid}.')
    else:
        print('[-] Web3 is not connected.')


if __name__ == '__main__':
    vault_cli()
