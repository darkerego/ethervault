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
SIGNERS = ['0xd6F1B722B6F58E421802Eb234AC81117819EB106', '0xe04b37D8aBFa1Ac24B3C93115Cf15BaA2612aCA1', '0xdA46715493B1a7b03409eee9ab233bca8454688f']
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

