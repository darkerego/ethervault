#!/usr/bin/python3
import os
import argparse
import json
import brownie
import dotenv
from brownie import *
from brownie import accounts
from brownie.network.contract import ContractContainer, Contract
from brownie import EtherVault
import dotenv

# EDIT THESE CONFIG VARIABLES


def config_loader(conf_file: str):
    with open(conf_file, 'r') as f:
        conf = json.load(f)
    account = conf.get('account')
    signers = conf.get('signers')
    threshold = conf.get('threshold')
    daily_dollar_limit = conf.get('daily_dollar_limit')
    return account, signers, threshold, daily_dollar_limit


CONF_FILE = 'configs/ethervault_deploy.json'
deploy_acct, signers, threshold, daily_eth_wei_limit = config_loader(CONF_FILE)
dotenv.load_dotenv()
ETHERSCAN_TOKEN = os.environ.get('ETHERSCAN_TOKEN')
acct = accounts.load(deploy_acct)


def deploy(signers: list, threshold: int, limit: int, acct=None):
    return EtherVault.deploy(signers, threshold, limit, {'from': acct.address}, publish_source=True)


def main():
    # args = argparse.ArgumentParser()
    return deploy(signers, threshold, daily_eth_wei_limit, acct=acct)


if __name__ == '__main__':
    main()
