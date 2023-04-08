#!/usr/bin/env python3
# Super Beta
import argparse
import os.path

import dotenv
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address, to_wei, to_hex, from_wei
from secure_web3 import sw3_wallet, sw3
from web3.contract import Contract

import vault_lib.gas_estimator
from vault_lib import eip1559_gas
from vault_lib import exceptions
from vault_lib import helpers
from vault_lib import vault_abi


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
            return self.w3.eth.contract(self.contract_address, abi=vault_abi.ethervault_2_abi)
        raise exceptions.ContractNotConfigured('Please specify your contract address on '
                                               'this network in your wallet file.')

    def build_contract_interaction_tx(self, function: str, *args) -> dict:
        """
        Builds contract interaction transaction.
        :param function: The function to call
        :param args: The arguments to that function
        :return: dict tx object
        """

        # max_pri_fee, max_fee = self.sw3_wallet.query_gas_api()
        encoded_data = self.contract.encodeABI(function, args=args)
        max_pri_fee, max_fee, gas_est = vault_lib.gas_estimator.gas_estimator(self.w3, self.sw3.account.address, self.contract.address,
                                                                              0.0, 'medium',self.contract, function, *args)
        print(f'[+] Priority Fee: {max_pri_fee}, Max: {max_fee}, Gas: {gas_est}')
        raw_txn = {
            "from": self.sw3.account.address,
            "gas": gas_est,  # 200000
            'maxPriorityFeePerGas': to_wei(max_pri_fee, 'gwei'),
            'maxFeePerGas': to_wei(max_fee, 'gwei'),
            "to": self.contract_address,
            "value": to_hex(0),
            "data": encoded_data,
            "nonce": self.w3.eth.get_transaction_count(self.sw3.account.address),
            "chainId": self.w3.eth.chain_id
        }
        return raw_txn

    def get_contract_nonce(self) -> int:
        return self.get_property('execNonce') +1

    def get_contract_balance(self) -> int:
        return self.sw3.w3.eth.get_balance(self.contract_address)

    def get_eth_account_balance(self, address):
        return self.w3.eth.get_balance(to_checksum_address(address))

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

    def add_tracked_token(self, token_address: (str, ChecksumAddress), price_feed_address: (str, ChecksumAddress)):
        tx = self.build_contract_interaction_tx('trackToken', to_checksum_address(token_address),
                                                to_checksum_address(price_feed_address), self.get_contract_nonce())
        return self.sw3_wallet.broadcast_raw_tx(tx=tx, private=False)

    def propose_withdrawal_raw(self, destination: ChecksumAddress, quantity: float, data: bytes = bytes('0x'.encode())):
        raw_qty = int(self.sw3.w3.toWei(quantity, 'ether'))

        assert (
                    self.get_contract_balance() >= raw_qty)
        #tx = self.build_contract_interaction_tx('submitTx', args={'recipient': to_checksum_address(destination),
        #                                                          'value': int(raw_qty), 'data': data,
        #                                                          '_nonce': int(self.get_contract_nonce())})
        tx = self.build_contract_interaction_tx('submitRawTx', to_checksum_address(destination), int(raw_qty), data, int(self.get_contract_nonce()))
        return self.sw3_wallet.broadcast_raw_tx(tx=tx, private=False)

    def propose_token_withdrawal_via_raw(self, destination: ChecksumAddress, token_address: ChecksumAddress, quantity: float):
        token = self.w3.eth.contract(token_address, abi=vault_lib.vault_abi.EIP20_ABI)
        decimals = token.functions.decimals().call()
        raw_qty = int(quantity * (10**decimals))
        #data = token.functions.transfer(to_checksum_address(destination), raw_qty).encodeABI()
        data = token.encodeABI('transfer', (to_checksum_address(destination), raw_qty))
        #tx = self.build_contract_interaction_tx('submitTx', args={'recipient': to_checksum_address(token_address),
        #                                                          'value': 0, 'data': data,
        #                                                          '_nonce': int(self.get_contract_nonce())})
        tx = self.build_contract_interaction_tx('submitRawTx', to_checksum_address(token_address), 0, data, int(self.get_contract_nonce()))
        return self.sw3_wallet.broadcast_raw_tx(tx=tx, private=False)

    def assert_version(self, _version: int = 2) -> bool:
        try:
            assert (self.get_property('version') == _version)
        except AssertionError:
            print('[!] Wrong version for function call.')
            return False
        return True

    def withdraw_via_withdraw(self, token_address: (ChecksumAddress, None), destination: ChecksumAddress, amount: float):
        self.assert_version(2)
        if token_address is None:
            raw_qty = int(amount * (10 ** 18))
            token_address = '0x0000000000000000000000000000000000000000'
        else:
            token = self.w3.eth.contract(token_address, abi=vault_lib.vault_abi.EIP20_ABI)
            decimals = token.functions.decimals().call()
            raw_qty = int(amount * (10 ** decimals))
        tx = self.build_contract_interaction_tx('withdraw', to_checksum_address(token_address), to_checksum_address(destination),
                                                raw_qty, int(self.get_contract_nonce()))
        return self.sw3_wallet.broadcast_raw_tx(tx=tx, private=False)




    def cancel_withdrawal(self, transaction_id: int) -> (hex, bool):
        nonce = self.get_contract_nonce()
        #tx = self.build_contract_interaction_tx('deleteTx', {'txid': transaction_id, '_nonce': nonce})
        tx = self.build_contract_interaction_tx('deleteTx', transaction_id, nonce)
        return self.sw3_wallet.broadcast_raw_tx(tx=tx, private=False)

    def confirm_withdrawal(self, transaction_id) -> (hex, bool):
        nonce = self.get_contract_nonce()
        # tx = self.build_contract_interaction_tx('approveTx', {'txid': transaction_id, '_nonce': nonce})
        tx = self.build_contract_interaction_tx('approveTx', transaction_id, nonce)
        return self.sw3_wallet.broadcast_raw_tx(tx=tx, private=False)

    def initiate_proposal(self, signer_address: ChecksumAddress, limit: float, threshold: int, paused: bool = False) -> (hex, bool):
        #tx = self.build_contract_interaction_tx('newProposal', {'_signer': signer_address, '_limit': limit,
        #                                                        '_threshold': threshold,
        #                                                        '_nonce': self.get_contract_nonce()})
        tx = self.build_contract_interaction_tx('newProposal', signer_address, limit, threshold, paused, self.get_contract_nonce())
        return self.sw3_wallet.broadcast_raw_tx(tx=tx, private=False)

    def approve_proposal(self, proposal_id) -> (hex, bool):
        #tx = self.build_contract_interaction_tx('approveProposal', {'_proposalId': proposal_id,
        #                                                            '_nonce': self.get_contract_nonce()})
        tx = self.build_contract_interaction_tx('approveProposal', proposal_id, self.get_contract_nonce())
        return self.sw3_wallet.broadcast_raw_tx(tx=tx, private=False)

    def revoke_proposal(self, proposal_id) -> (hex, bool):
        #tx = self.build_contract_interaction_tx('deleteProposal', {'_proposalId': proposal_id,
        #                                                           '_nonce': self.get_contract_nonce()})
        tx = self.build_contract_interaction_tx('deleteProposal', proposal_id, self.get_contract_nonce())
        return self.sw3_wallet.broadcast_raw_tx(tx=tx, private=False)

    def get_ethervault_version(self):
        return self.get_property('version')

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
    args.add_argument('-n', '--network', type=str, default='goerli', choices=['goerli', 'ethereum', 'arbitrum'],
                      help='The EVM chain to operate on.')
    subparsers = args.add_subparsers(dest='command')
    deposit = subparsers.add_parser('deposit', help='Deposit ether')
    deposit.add_argument('-q', '--quantity', type=float, help='Ether amount')
    track = subparsers.add_parser('track_token')
    track.add_argument('-ta', '--token-address', dest='token_address', type=str, default=None, help='The ERC20 token address.')
    track.add_argument('-fa', '--feed-address', dest='feed_address', type=str, default=None,
                       help='Chainlink oracle address.')

    withdraw = subparsers.add_parser('withdraw', help='Propose a withdrawal.')
    withdraw.add_argument('-r', '--recipient', type=str, help='Ether address of recipient.')
    withdraw.add_argument('-q', '--quantity', type=float, help='Ether amount.')
    withdraw.add_argument('-f', '--file', type=str, help='A file with data for transaction.')
    withdraw_token = subparsers.add_parser('withdraw_token', help='Withdraw ERC20 token')
    withdraw_token.add_argument('-r', '--recipient', type=str, default=None,
                                help='Address to send tokens.')
    withdraw_token.add_argument('-t', '--token-address', dest='token_address', type=str,
                                help='The ERC20 token address.')
    withdraw_token.add_argument('-q', '--quantity', type=float, default=0.0, help='The amount to withdraw.')
    cancel = subparsers.add_parser('cancel', help='Cancel a pending transaction.')
    cancel.add_argument('-t', '--txid', help='The transaction ID.')
    confirm = subparsers.add_parser('confirm', help='Confirm a transaction.')
    confirm.add_argument('-t', '--txid', help='The transaction ID.')
    init_proposal = subparsers.add_parser('proposal', help='Create a new proposal.')
    init_proposal.add_argument('-s', '--signer', type=str, default=None, help='Signer address to add or revoke.')
    init_proposal.add_argument('-t', '--threshold', type=int, default=0, help='Proposed new threshold.')
    init_proposal.add_argument('-l', '--limit', type=float, default=0, help='Proposed new daily spending limit.')
    init_proposal.add_argument('-p', '--paused', type=bool, default=False, help='Propose to pause the contract.')
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
    balances = subparsers.add_parser('balance', help='Get balance of the contract or another address.')
    balances.add_argument('-a', '--address', type=str, default=None, help='Balance of this account.')


    args = args.parse_args()
    # print(args)
    dotenv.load_dotenv()
    contract_address = os.environ.get(f'ethervault_{args.network}')
    print(f'[+] Contract is:  {contract_address}')
    print(f'[+] Loading wallet "{args.wallet}"')
    if args.command in ['deposit', 'withdraw', 'cancel', 'confirm', 'proposal', 'revoke', 'approve', 'withdraw_token',
                        'track_token']:
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

    if args.command == 'track_token':
        print('[+] NOTICE: Only EtherVaultL2 has this function.')
        print('[+] Configuring new tracked token with parameters: ')
        print('[+] Token Address:', args.token_address)
        print('[+] Oracle Address: ', args.feed_address)
        helpers.parse_tx_ret_val(vault.add_tracked_token(args.token_address, args.feed_address))

    if args.command == 'withdraw':
        ev_version = vault.get_ethervault_version()
        if ev_version == 1:
            print(f'[+] Will propose new withdrawal with parameters:')
            print(f'[+] Recipient: {args.recipient}')
            print(f'[+] Ether value: {args.quantity}')
            print(f'[+] File with transaction data: {args.file}')
            if args.file:
                data = bytes(helpers.read_data(args.file).encode())
                print(f'[+] Read {len(data)} bytes from {args.file}')
            else:
                data = b'0x'
            helpers.parse_tx_ret_val(vault.propose_withdrawal_raw(to_checksum_address(args.recipient), args.quantity, data))
        else:
            print(f'[+] Will propose new ETH withdrawal with parameters:')
            print(f'[+] Recipient: {args.recipient}')
            print(f'[+] Ether value: {args.quantity}')
            ret = vault.withdraw_via_withdraw('0x0000000000000000000000000000000000000000', args.recipient, args.quantity)
            helpers.parse_tx_ret_val(ret)

    if args.command == 'withdraw_token':
        ev_version = vault.get_ethervault_version()
        print(f'[+] Will propose new token withdrawal with parameters: ')
        print(f'[+] Recipient: {args.recipient}')
        print(f'[+] Token: {args.token_address}')
        print(f'[+] Quantity: {args.quantity}')
        if ev_version == 1:
            helpers.parse_tx_ret_val(vault.propose_token_withdrawal_via_raw(args.recipient, args.token_address, args.quantity))
        else:
            helpers.parse_tx_ret_val(vault.withdraw_via_withdraw(args.token_address, args.recipient, args.quantity))

    if args.command == 'cancel':
        print(f'[+] Canceling pending transaction with txid: {args.txid}')
        helpers.parse_tx_ret_val(ret = vault.cancel_withdrawal(args.txid))

    if args.command == 'confirm':
        print(f'[+] Confirming transaction with txid {args.txid} using the key: {args.wallet}')
        helpers.parse_tx_ret_val(ret = vault.confirm_withdrawal(int(args.txid)))

    if args.command == 'proposal':
        if args.signer is None:
            args.signer = '0x0000000000000000000000000000000000000000'
        if args.limit:
            args.limit = to_wei(args.limit, 'ether')

        print(f'[+] Will create a new proposal with the following parameters:')
        print(f'[+] Signer (addition/revocation): {args.signer}')
        print(f'[+] New threshold: {args.threshold}')
        print(f'[+] New daily limit: {args.limit}')
        helpers.parse_tx_ret_val(vault.initiate_proposal(to_checksum_address(args.signer), int(args.limit), int(args.threshold)))

    if args.command == 'approve':
        print(f'[+] Approving pending proposal with ID: {args.id}')
        helpers.parse_tx_ret_val(vault.approve_proposal(args.id))

    if args.command == 'revoke':
        print(f'[+] Revoking pending proposal with ID: {args.id}')
        helpers.parse_tx_ret_val(vault.revoke_proposal(args.id))

    if args.command == 'getprop':
        print(f'[+] Calling contract to get the value of property {args.name}')
        ret = vault.get_property(args.name, int(args.id))
        print(f'[+] Result:\n{ret}')

    if args.command == 'balance':
        if args.address:
            print(f'[+] Balance of {args.address}: {vault.get_eth_account_balance(args.address)}')
        else:
            balance = from_wei(vault.get_contract_balance(), 'ether')
            print(f'[+] Balance: {balance}')


if __name__ == '__main__':
    vault_cli()
