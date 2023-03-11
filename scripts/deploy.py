#!/usr/bin/python3
import os
import argparse

import brownie
import dotenv
from brownie import *
from brownie import accounts
from brownie.network.contract import ContractContainer,Contract
from brownie import EtherVault
import dotenv

# EDIT THESE CONFIG VARIABLES
DEPLOY_ACCT = '0xF00F00'
SIGNERS = ['0xF00F00', '0xF00F01', '0xF00F02']
THRESHOLD = 2
DAILY_LIMIT = 0.05 * (10**18)


dotenv.load_dotenv()
ETHERSCAN_TOKEN = os.environ.get('ETHERSCAN_TOKEN')
acct = accounts.load(DEPLOY_ACCT)


def deploy(signers: list, threshold: int, limit: int, acct = None):
    return EtherVault.deploy(signers, threshold, limit, {'from': acct.address}, publish_source=True)


def main():
    return deploy(SIGNERS, THRESHOLD, DAILY_LIMIT, acct=acct)


if __name__ == '__main__':
    main()

