# PLEASE GO THROUGH THE README.md FILE BEFORE RUNNING THE CODE ##

# import Web3 class from web3 module
import decimal

#from eth_defi.token import fetch_erc20_details
from eth_typing import ChecksumAddress
from eth_utils import to_wei, from_wei
import web3
from web3.contract import Contract

from vault_lib.vault_abi import EIP20_ABI
from web3 import Web3, HTTPProvider
# import the in-built statistics module
import statistics


# Setting node endpoint value
# CHAINSTACK_NODE_ENDPOINT = '<NODE_ENDPOINT>'


def gas_estimator(w3: web3.Web3, from_account: ChecksumAddress, to_account:ChecksumAddress, eth_value: float, priority: str, contract: Contract, fn: str, *_args):
    print(f'Selected: {priority}')

    if priority == 'polygon':
        priority = 'high'
        poly_fix = True
    else:
        poly_fix = False
    BASEFEE_PERCENTAGE_MULTIPLIER = {
        "low": 1.10,  # 10% increase
        "medium": 1.20,  # 20% increase
        "high": 1.25  # 25% increase
    }

    PRIORITY_FEE_PERCENTAGE_MULTIPLIER = {
        "low": .94,  # 6% decrease
        "medium": .97,  # 3% decrease
        "high": .98  # 2% decrease
    }

    MINIMUM_FEE = {
        "low": 100000000,
        "medium": 150000000,
        "high": 200000000

    }

    #  a dictionary for storing the sorted priority fee
    feeByPriority = {
        "low": [],
        "medium": [],
        "high": []
    }
    feeHistory = w3.eth.fee_history(5, 'latest', [10, 20, 30])

    # get the basefeepergas of the latest block
    latestBaseFeePerGas = feeHistory["baseFeePerGas"][-1]
    if contract is None:
        estimate_gasUsed = w3.eth.estimate_gas(
            {'to': to_account, 'from': from_account,
             'value': to_wei(int(eth_value), "ether")})
    else:
        function = getattr(contract.functions, fn)
        try:
            estimate_gasUsed = function(*_args).estimate_gas({'from': from_account})
        except web3.exceptions.ContractLogicError as err:
            print(f'[!] Contract Logic Error with gas estimation: {err}')
            return 0, 0, 0

    for feeList in feeHistory["reward"]:
        # 10 percentile values - low fees
        feeByPriority["low"].append(feeList[0])
        # 20 percentile value - medium fees
        feeByPriority["medium"].append(feeList[1])
        # 30 percentile value - high fees
        feeByPriority["high"].append(feeList[2])
    for key in feeByPriority:
        # adjust the basefee,
        # use the multiplier value corresponding to the key
        adjustedBaseFee = latestBaseFeePerGas * BASEFEE_PERCENTAGE_MULTIPLIER[key]

        # get the median of the priority fee based on the key
        medianOfFeeList = statistics.median(feeByPriority[key])

        # adjust the median value,
        # use the multiplier value corresponding to the key
        adjustedFeeMedian = (
                medianOfFeeList * PRIORITY_FEE_PERCENTAGE_MULTIPLIER[key])

        # if the adjustedFeeMedian falls below the MINIMUM_FEE,
        # use the MINIMUM_FEE value,
        adjustedFeeMedian = adjustedFeeMedian if adjustedFeeMedian > MINIMUM_FEE[
            key] else MINIMUM_FEE[key]

        suggestedMaxPriorityFeePerGasGwei = from_wei(adjustedFeeMedian, "gwei")
        if poly_fix:
            suggestedMaxPriorityFeePerGasGwei = suggestedMaxPriorityFeePerGasGwei * 5
        # [optional] round the amount
        suggestedMaxPriorityFeePerGasGwei = round(
            suggestedMaxPriorityFeePerGasGwei, 5)
        # calculate the Max fee per gas
        suggestedMaxFeePerGas = (adjustedBaseFee + adjustedFeeMedian)
        # convert to gwei denomination
        suggestedMaxFeePerGasGwei = from_wei(suggestedMaxFeePerGas, "gwei")
        if poly_fix:
            suggestedMaxFeePerGasGwei = suggestedMaxFeePerGasGwei * 3
        # [optional] round the amount to the given decimal precision
        suggestedMaxFeePerGasGwei = round(suggestedMaxFeePerGasGwei, 9)
        # calculate the total gas fee
        totalGasFee = suggestedMaxFeePerGasGwei * estimate_gasUsed
        # convert the value to gwei denomination
        totalGasFeeGwei = from_wei(totalGasFee, "gwei")
        # [optional] round the amount
        totalGasFeeGwei = round(totalGasFeeGwei, 8)
        pr = f"PRIORITY: {key.upper()}\nMAX PRIORITY FEE (GWEI): {suggestedMaxPriorityFeePerGasGwei}"
        pr += f"\nMAX FEE (GWEI) : {suggestedMaxFeePerGasGwei}\nGAS PRICE (ETH): {totalGasFeeGwei}, wei: {totalGasFee}"
        print(pr)
        print("=" * 80)  # guess what this does ?

        if key.upper() == priority.upper():
            # print()
            return suggestedMaxPriorityFeePerGasGwei, suggestedMaxFeePerGasGwei, estimate_gasUsed