#!/usr/bin/python3
import json
import os
import argparse

import brownie
import dotenv
from brownie import *
from brownie import accounts
from brownie.network.contract import ContractContainer,Contract
from brownie import EtherVaultL2
import dotenv

# EDIT THESE CONFIG VARIABLES
from eth_utils import to_checksum_address

def config_loader(conf_file: str):
    with open(conf_file, 'r') as f:
        conf = json.load(f)
    account = conf.get('account')
    signers = conf.get('signers')
    threshold = conf.get('threshold')
    daily_dollar_limit = conf.get('daily_dollar_limit')
    eth_oracle = conf.get('eth_oracle')
    return account, signers, threshold, daily_dollar_limit, eth_oracle


CONF_FILE = 'configs/ethervaultl2_deploy.json'
deploy_acct, signers, threshold, daily_dollar_limit, eth_oracle = config_loader(CONF_FILE)
dotenv.load_dotenv()
ETHERSCAN_TOKEN = os.environ.get('ETHERSCAN_TOKEN')
acct = accounts.load(deploy_acct)


def deploy(signers: list, threshold: int, limit: int, eth_feed, acct = None):
    return EtherVaultL2.deploy(signers, threshold, limit, eth_feed, {'from': acct.address}, publish_source=True)


def verify(contract_addr):
    # in case it fails the first time
    EtherVaultL2.publish_source(EtherVaultL2.at(to_checksum_address(contract_addr)))


def main():
    # args = argparse.ArgumentParser()
    return deploy(signers, threshold, daily_dollar_limit, eth_oracle, acct=acct)


if __name__ == '__main__':
    """args = argparse.ArgumentParser()
    subparsers = args.add_subparsers(dest='command')
    _deploy = subparsers.add_parser('deploy')
     args = args.parse_args()"""
    main()
