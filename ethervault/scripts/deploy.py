#!/usr/bin/python3
import os
import argparse
import dotenv
from brownie import *
from brownie import accounts
from brownie.network.contract import ContractContainer,Contract
from brownie import Ethervault
import dotenv
dotenv.load_dotenv()
ETHERSCAN_TOKEN=os.environ.get('ETHERSCAN_TOKEN')
acct = accounts.load(os.environ.get('DEPLOYER_ACCT'))


def main():
    return Ethervault.deploy({'from': os.environ.get('DEPLOYER_ACCT')}, publish_source=True)


if __name__ == '__main__':
    main()