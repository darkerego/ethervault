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
DEPLOY_ACCT = 'deployer2'
SIGNERS = ['0xF738Be6972c384211Da31fCAb979F1F81CB1397E', '0x7612E93FF157d1973D0f95Be9E4f0bdF93BAf0DE', '0x2aB5BA5611f4cc435755860d19B94e35B277C5AF']
THRESHOLD = 2
DAILY_LIMIT = 0.05 * (10**18)


dotenv.load_dotenv()
ETHERSCAN_TOKEN = os.environ.get('ETHERSCAN_TOKEN')
acct = accounts.load(DEPLOY_ACCT)


def deploy(signers: list, threshold: int, limit: int, acct = None):
    return EtherVault.deploy(signers, threshold, limit, {'from': acct.address}, publish_source=True)


def main():
    # args = argparse.ArgumentParser()
    return deploy(SIGNERS, THRESHOLD, DAILY_LIMIT, acct=acct)


if __name__ == '__main__':
    main()

