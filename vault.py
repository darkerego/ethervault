#!/usr/bin/env python3
# Super Beta
import argparse
import os.path

import dotenv
from eth_typing import ChecksumAddress
from secure_web3 import sw3_wallet, sw3
from web3.contract import Contract

from vault_lib import exceptions
from vault_lib import vault_abi
from vault_lib import json_funcs
import secure_web3.sw3_wallet


class VaultCli:
    def __init__(self, wallet_file: str, network: str = 'ethereum', init: (bool, str, ChecksumAddress) = False):
        """
        Command Line Ethervault controller tool
        (note: see docs)

        Tool for deploying, depositing, administering the contract.
        :param wallet_file: json wallet file
        :param network: ie "ethereum"
        :param init: import private key and setup wallet
        """
        dotenv.load_dotenv('.env')
        self.contract_address = None
        self.wallet_file = wallet_file
        self.network = network
        self.sw3 = sw3.SecureWeb3(wallet_file, network, )
        self._w3 = sw3.SecureWeb3.w3

        if not self.check_wallet(init):
            return
        self.sw3.load_wallet(self.wallet_file)
        self.sw3.setup_w3()
        self.sw3_wallet = sw3_wallet.EtherShellWallet(self.sw3)

    def check_wallet(self, init: (bool, str, ChecksumAddress) = False) -> bool:
        """

        :param init: if specified, store in wallet this contract address
        :return: bool
        """
        if init:
            return self.configure_wallet(init)
        if not os.path.exists(self.wallet_file):
            print(f'[!] Wallet does not exist: {self.wallet_file}')
            return False
        #contract = json_funcs.load_json(self.wallet_file).get('contract').get('address')
        return True

    def configure_wallet(self, init) -> bool:
        """

        :return:
        """
        print('[+] Configuring .. ')
        custom_params = []
        if os.environ.get(f'ethervault_{self.network}'):
            custom_params = [{"contract": {'address': init, 'networks': [self.network]}, 'nonce': 0}]
        if self.sw3.configure_wallet(custom_params):
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

    @property
    def contract(self) -> Contract:
        if hasattr(self, 'contract_address'):
            return self._w3.eth.contract(self.contract_address, abi=vault_abi.vault_abi)
        raise exceptions.ContractNotConfigured('Please specify your contract address on '
                                               'this network in your wallet file.')

    def deploy_contract(self, signers: list, threshold: int, daily_limit: int) -> None:
        from scripts import deploy
        deploy.deploy(signers, threshold, daily_limit, self.sw3.account)

    def build_contract_interaction_tx(self, function: str, args: dict) -> dict:
        """
        Builds contract interaction transaction.
        :param function: The function to call
        :param args: The arguments to that function
        :return: dict tx object
        """
        contract = self.contract
        fn = getattr(contract.functions, function)
        args.update({'_nonce': self.get_contract_nonce() + 1})
        est_gas = fn(args).estimate_gas({'from': self.sw3.account.address})
        max_pri_fee, max_fee = self.sw3_wallet.query_gas_api()
        tx = fn(args).build_transaction({'from': self.sw3.account.address, 'gas': est_gas,
                                         'maxFeePerGas': max_fee, 'maxPriorityFeePerGas': max_pri_fee})
        return tx

    def get_contract_nonce(self) -> int:
        return self.contract.functions.execNonce.call()

    def get_contract_balance(self) -> int:
        return self.sw3.w3.eth.get_balance(self.contract_address)

    def deposit_ether(self, qty: float) -> (hex, bool):
        """
        Deposit in contract
        :param qty:
        :return: hex(txid)
        """
        # TODO: test this function
        raw_qty = int(qty * 10**18)
        txid = self.sw3_wallet.send_eth(raw_qty, self.contract_address, False, False)
        if txid:
            print(f'[+] TXID: {txid}')

    def propose_withdrawal(self, destination: ChecksumAddress, quantity: float, data: bytes = bytes('0x')):
        raw_qty = self.sw3.w3.toWei(quantity, 'ether')
        assert(self.get_contract_balance() >= raw_qty)
        tx = self.build_contract_interaction_tx('submitTx', {'recipient': destination, 'value': raw_qty, 'data': data,
                                                             '_nonce': self.get_contract_nonce() + 1})
        return self.sw3_wallet.broadcast_raw_tx(tx=tx, private=False)

    def revoke_withdrawal(self, transaction_id: int) -> (hex, bool):
        pass

    def confirm_withdrawal(self) -> (hex, bool):
        pass

    def initiate_proposal(self, signer_address: ChecksumAddress, limit: float, threshold: int) -> (hex, bool):
        pass

    def approve_proposal(self, proposal_id) -> (hex, bool):
        pass

    def revoke_proposal(self, proposal_id) -> (hex, bool):
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
    deploy = subparsers.add_parser('deploy', help='Deploy contract')
    deploy.add_argument('-s', '--signers', type=str, nargs='+',
                        help='Signer accounts, space separated')
    deploy.add_argument('-T', '--threshold', type=int, help='Threshold to move funds')
    deploy.add_argument('-L', '--limit', type=int, help='Daily withdrawal limit value in wei')
    args = args.parse_args()
    vault = VaultCli('keys/default_wallet.json')
    print('[!] Warning: this is really alpha and not everything is implemented yet.')

    if args.init:
        print('[+] The setup wizard will create your wallet now ... Enter an encryption password. ')
        vault.configure_wallet(args.init)

    if args.deploy:
        print(args.deploy)

    cid = vault.check_w3_chain_id()
    if cid:
        print(f'[+] Web3 is connected to {cid}.')
    else:
        print('[-] Web3 is not connected.')


if __name__ == '__main__':
    vault_cli()
