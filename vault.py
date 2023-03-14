#!/usr/bin/env python3
# Super Beta
import argparse
import os.path

import brownie
import dotenv
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address, to_wei, to_hex, from_wei
from secure_web3 import sw3_wallet, sw3
from web3.contract import Contract

from vault_lib import exceptions
from vault_lib import vault_abi
from vault_lib import json_funcs
from vault_lib import helpers
import secure_web3.sw3_wallet


class VaultCli:
    def __init__(self, wallet_file: str, network: str = 'ethereum', contract_address: str = None, init: bool = False,
                 require_unlock: bool = True):
        """
        Command Line Ethervault controller tool
        (note: see docs)

        Tool for deploying, depositing, administering the contract.
        :param wallet_file: json wallet file
        :param network: ie "ethereum"
        :param init: import private key and setup wallet
        """
        dotenv.load_dotenv('.env')
        self.contract_address = contract_address
        self.wallet_file = wallet_file
        self.network = network
        self.contract_nonce = 0
        self.sw3 = sw3.SecureWeb3(wallet_file, network, )

        if require_unlock:
            if not init:
                self.sw3.load_wallet(self.wallet_file)
            else:
                if not self.check_wallet(init):
                    return

        self.contract_address = contract_address
        self.sw3.setup_w3()
        self.sw3_wallet = sw3_wallet.EtherShellWallet(self.sw3)

    def check_wallet(self, init: (bool, str, ChecksumAddress) = False) -> bool:
        """

        :param init: if specified, store in wallet this contract address
        :return: bool
        """
        if init:
            return self.configure_wallet()
        if not os.path.exists(self.wallet_file):
            print(f'[!] Wallet does not exist: {self.wallet_file}')
            return False
        return True

    def configure_wallet(self) -> bool:
        """

        :return:
        """
        print('[+] Configuring .. ')
        custom_params = []
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
    def w3(self):
        return self.sw3._w3

    @property
    def contract(self) -> Contract:
        if hasattr(self, 'contract_address'):
            return self.w3.eth.contract(self.contract_address, abi=vault_abi.vault_abi)
        raise exceptions.ContractNotConfigured('Please specify your contract address on '
                                               'this network in your wallet file.')

    def build_contract_interaction_tx(self, function: str, args) -> dict:
        """
        Builds contract interaction transaction.
        :param function: The function to call
        :param args: The arguments to that function
        :return: dict tx object
        """
        # print(args)
        contract = self.contract
        # fn = getattr(contract.functions, function)
        # args.update({'_nonce': self.get_contract_nonce() + 1})
        # est_gas = fn(args).estimate_gas({'from': self.sw3.account.address})
        max_pri_fee, max_fee = self.sw3_wallet.query_gas_api()
        raw_txn = {
            "from": self.sw3.account.address,
            "gas": 200000,  # 200000
            'maxPriorityFeePerGas': to_wei(max_pri_fee, 'gwei'),
            'maxFeePerGas': to_wei(max_fee, 'gwei'),
            "to": self.contract_address,
            "value": to_hex(0),
            "data": self.contract.encodeABI(function, args=args),
            "nonce": self.w3.eth.get_transaction_count(self.sw3.account.address),
            "chainId": self.w3.eth.chain_id
        }
        return raw_txn

    def get_contract_nonce(self) -> int:
        return self.get_property('execNonce') +1

    def get_contract_balance(self) -> int:
        return self.sw3.w3.eth.get_balance(self.contract_address)

    def deposit_ether(self, qty: float) -> (hex, bool):
        """
        Deposit in contract
        :param qty:
        :return: hex(txid)
        """
        # TODO: test this function
        raw_qty = to_wei(qty, 'ether')
        txid = self.sw3_wallet.send_eth(raw_qty, self.contract_address, False, False)
        if txid:
            print(f'[+] TXID: {txid}')

    def propose_withdrawal(self, destination: ChecksumAddress, quantity: float, data: bytes = bytes('0x'.encode())):
        raw_qty = int(self.sw3.w3.toWei(quantity, 'ether'))

        assert (
                    self.get_contract_balance() >= raw_qty)  # [to_checksum_address(destination), int(raw_qty), bytes(data), int(self.get_contract_nonce()+1)]
        tx = self.build_contract_interaction_tx('submitTx', args={'recipient': to_checksum_address(destination),
                                                                  'value': int(raw_qty), 'data': bytes(data),
                                                                  '_nonce': int(self.get_contract_nonce())})
        return self.sw3_wallet.broadcast_raw_tx(tx=tx, private=False)

    def cancel_withdrawal(self, transaction_id: int) -> (hex, bool):
        nonce = self.get_contract_nonce()
        tx = self.build_contract_interaction_tx('deleteTx', {'txid': transaction_id, '_nonce': nonce})
        return self.sw3_wallet.broadcast_raw_tx(tx=tx, private=False)

    def confirm_withdrawal(self, transaction_id) -> (hex, bool):
        nonce = self.get_contract_nonce()
        tx = self.build_contract_interaction_tx('approveTx', {'txid': transaction_id, '_nonce': nonce})
        return self.sw3_wallet.broadcast_raw_tx(tx=tx, private=False)

    def initiate_proposal(self, signer_address: ChecksumAddress, limit: float, threshold: int) -> (hex, bool):
        tx = self.build_contract_interaction_tx('newProposal', {'_signer': signer_address, '_limit': limit,
                                                                '_threshold': threshold,
                                                                '_nonce': self.get_contract_nonce()})
        return self.sw3_wallet.broadcast_raw_tx(tx=tx, private=False)

    def approve_proposal(self, proposal_id) -> (hex, bool):
        tx = self.build_contract_interaction_tx('approveProposal', {'_proposal_id': proposal_id,
                                                                    '_nonce': self.get_contract_nonce()})
        return self.sw3_wallet.broadcast_raw_tx(tx=tx, private=False)

    def revoke_proposal(self, proposal_id) -> (hex, bool):
        tx = self.build_contract_interaction_tx('deleteProposal', {'_proposal_id': proposal_id,
                                                                   '_nonce': self.get_contract_nonce()})
        return self.sw3_wallet.broadcast_raw_tx(tx=tx, private=False)

    def get_property(self, name, _id=None):
        contract = self.contract
        method = getattr(contract.functions, name)
        if _id is None:
            return method().call()
        return method(_id).call()


def vault_cli():
    unlock = False
    args = argparse.ArgumentParser()
    args.add_argument('-w', '--wallet', type=str, default='keys/default_wallet.json')
    args.add_argument('-i', '--init', action='store_true', help='Import private key and initialize the wallet.')
    args.add_argument('-n', '--network', type=str, default='goerli', choices=['goerli', 'ethereum'],
                      help='The EVM chain to operate on.')
    subparsers = args.add_subparsers(dest='command')
    deposit = subparsers.add_parser('deposit', help='Deposit ether')
    deposit.add_argument('-q', '--quantity', type=float, help='Ether amount')
    transaction = subparsers.add_parser('withdraw', help='Propose a withdrawal.')
    transaction.add_argument('-r', '--recipient', type=str, help='Ether address of recipient.')
    transaction.add_argument('-q', '--quantity', type=float, help='Ether amount.')
    transaction.add_argument('-f', '--file', type=str, help='A file with data for transaction.')
    cancel = subparsers.add_parser('cancel', help='Cancel a pending transaction.')
    cancel.add_argument('-t', '--txid', help='The transaction ID.')
    confirm = subparsers.add_parser('confirm', help='Confirm a transaction.')
    confirm.add_argument('-t', '--txid', help='The transaction ID.')
    init_proposal = subparsers.add_parser('proposal', help='Create a new proposal.')
    init_proposal.add_argument('-s', '--signer', type=str, help='Signer address to add or revoke.')
    init_proposal.add_argument('-t', '--threshold', type=int, help='Proposed new threshold.')
    init_proposal.add_argument('-l', '--limit', type=float, help='Proposed new daily spending limit.')
    approve = subparsers.add_parser('approve', help='Approve a pending proposal.')
    approve.add_argument('-i', '--id', type=int, help='The pending proposal ID.')
    revoke = subparsers.add_parser('revoke', help='Revoke a pending proposal.')
    revoke.add_argument('-i', '--id', type=int, help='The pending proposal ID.')
    getprop = subparsers.add_parser('getprop', help='Get public property value from contract.')
    getprop.add_argument('-n', '--name', type=str,
                         choices=['dailyLimit', 'execNonce', 'pendingProposals', 'pendingTxs', 'proposalId',
                                  'signerCount',
                                  'spentToday', 'threshold'], help='Name of property to get value.')
    getprop.add_argument('-i', '--id', help='ID parameter for pending tx/proposal methods.')
    subparsers.add_parser('balance', help='Get balance of the contract.')

    args = args.parse_args()
    # print(args)
    dotenv.load_dotenv()
    contract_address = os.environ.get(f'ethervault_{args.network}')
    print(f'[+] Contract is:  {contract_address}')
    print(f'[+] Loading wallet "{args.wallet}"')
    if args.command in ['deposit', 'withdraw', 'cancel', 'confirm', 'propose', 'revoke', 'approve']:
        unlock = True

    vault = VaultCli(args.wallet, args.network, contract_address, args.init, unlock)
    cid = vault.check_w3_chain_id()
    if cid:
        print(f'[+] Web3 is connected to {cid}.')
    else:
        print('[-] Web3 is not connected.')

    print('[!] Warning: this is really alpha software and not everything is implemented yet!')

    if args.command == 'deposit':
        print(f'[+] Will deposit {args.quantity} to {contract_address}')
        vault.deposit_ether(qty=args.quantity)

    if args.command == 'withdraw':
        print(f'[+] Will propose new withdrawal with parameters:')
        print(f'[+] Recipient: {args.recipient}')
        print(f'[+] Ether value: {args.quantity}')
        print(f'[+] File with transaction data: {args.file}')
        if args.file:
            data = helpers.read_data(args.file)
            print(f'[+] Read {len(data)} bytes from {args.file}')
        else:
            data = b'0x'
        ret = vault.propose_withdrawal(to_checksum_address(args.recipient), args.quantity, data)
        if ret:
            print(f'[+] TXID: {ret}')

    if args.command == 'cancel':
        print(f'[+] Canceling pending transaction with txid: {args.txid}')
        ret = vault.cancel_withdrawal(args.txid)
        if ret:
            print(f'[+] TXID: {ret}')

    if args.command == 'confirm':
        print(f'[+] Confirming transaction with txid {args.txid} using the key: {args.wallet}')
        ret = vault.confirm_withdrawal(int(args.txid))
        if ret:
            print(f'[+] TXID: {ret}')

    if args.command == 'proposal':
        print(f'[+] Will create a new proposal with the following parameters:')
        print(f'[+] Signer (addition/revokation): {args.signer}')
        print(f'[+] New threshold: {args.threshold}')
        print(f'[+] New daily limit: {args.limit}')
        ret = vault.initiate_proposal(args.signers, args.limit, args.threshold)
        if ret:
            print(f'[+] TXID: {ret}')

    if args.command == 'approve':
        print(f'[+] Approving pending proposal with ID: {args.id}')
        ret = vault.approve_proposal(args.id)
        if ret:
            print(f'[+] TXID: {ret}')

    if args.command == 'revoke':
        print(f'[+] Revoking pending proposal with ID: {args.id}')
        ret = vault.revoke_proposal(args.id)
        if ret:
            print(f'[+] TXID: {ret}')

    if args.command == 'getprop':
        print(f'[+] Calling contract to get the value of property {args.name}')
        ret = vault.get_property(args.name, int(args.id))
        print(f'[+] Result:\n{ret}')

    if args.command == 'balance':
        balance = from_wei(vault.get_contract_balance(), 'ether')
        print(f'[+] Balance: {balance}')


if __name__ == '__main__':
    vault_cli()
