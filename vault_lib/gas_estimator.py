# PLEASE GO THROUGH THE README.md FILE BEFORE RUNNING THE CODE ##

# import Web3 class from web3 module
import decimal

#from eth_defi.token import fetch_erc20_details
from eth_utils import to_wei, from_wei

from vault_lib.vault_abi import EIP20_ABI
from web3 import Web3, HTTPProvider
# import the in-built statistics module
import statistics


# Setting node endpoint value
# CHAINSTACK_NODE_ENDPOINT = '<NODE_ENDPOINT>'


def gas_estimator(web3, FROM_ACCOUNT, TO_ACCOUNT, ETH_VALUE, priority='low', contract_address=None, tx_data = b'0x'):
    print(f'Selected: {priority}')
    # infura_key = '52f5c5e784084cda96d25869c09704ef'
    # web3 = Web3(HTTPProvider(f'https://goerli.infura.io/v3/{infura_key}'))
    # Setting account addressess
    # you can copy the account addresses from metamask]

    # FROM_ACCOUNT = "<FROM_ACCOUNT_ADDRESS>"
    # TO_ACCOUNT = "<TO_ACCOUNT_ADDRESS>"

    # setting the values for gas fee estimation.
    # The values are based on the metamask code

    # Setting the percentage multiplier for the basefee
    # The base fee is adjusted by INCREASING the value,
    # thus the percentage multiplier is calculated using the formula
    #       PERCENTAGE MULTIPLIER = 1 + percentage value ,
    # 10 % increase means, PERCENTAGE MULTIPLIER = 1 + (10/100)
    # the multipliers are chosen according to the priority [low , medium , high]
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

    # Setting the percentage multiplier for the priority fee
    # priority fee median is adjusted by DECREASING the value,
    # the percentage multiplier is calculated using the formula
    #       PERCENTAGE MULTIPLIER = 1 - percentage value,
    # 6 % decrease means, PERCENTAGE MULTIPLIER = 1 - (6/100)
    # the multipliers are chosen according to the priority [low , medium , high]
    PRIORITY_FEE_PERCENTAGE_MULTIPLIER = {
        "low": .94,  # 6% decrease
        "medium": .97,  # 3% decrease
        "high": .98  # 2% decrease
    }

    # the minimum PRIORITY FEE that should be payed,
    #  corresponding to the user priority (in WEI denomination)
    MINIMUM_FEE = {
        "low": 1000000000,
        "medium": 1500000000,
        "high": 2000000000

    }

    #  a dictionary for storing the sorted priority fee
    feeByPriority = {
        "low": [],
        "medium": [],
        "high": []
    }

    # HTTPProvider:
    # w3 = Web3(Web3.HTTPProvider(CHAINSTACK_NODE_ENDPOINT))
    w3 = web3

    # parameters :
    # Number of  blocks - 5
    # newest block in the provided range -
    #    latest [or you can give the latest block number]
    # reward_percentiles - 10,20,30 [ based on metamask]
    feeHistory = w3.eth.fee_history(5, 'latest', [10, 20, 30])

    # get the basefeepergas of the latest block
    latestBaseFeePerGas = feeHistory["baseFeePerGas"][-1]

    # Setting the ether value to be transferred
    # ETH_VALUE = .5
    # Calculating the estimated usage of gas in the following transaction
    if contract_address is None:
        estimate_gasUsed = w3.eth.estimate_gas(
            {'to': TO_ACCOUNT, 'from': FROM_ACCOUNT,
             'value': to_wei(int(ETH_VALUE), "ether"), 'data': tx_data})
    else:

        _abi = EIP20_ABI
        unicorns = web3.eth.contract(address=contract_address, abi=_abi)
        # token_details = fetch_erc20_details(web3, contract_address)
        # raw_amount = token_details.convert_to_raw(decimal.Decimal(ETH_VALUE))
        estimate_gasUsed = unicorns.functions.transfer(TO_ACCOUNT, int(ETH_VALUE)).estimate_gas(
            {'from': FROM_ACCOUNT})
        #estimate_gasUsed = w3.eth.estimate_gas(
        #    {'to': TO_ACCOUNT, 'from': FROM_ACCOUNT,
        #     'value': w3.to_wei(ETH_VALUE, "ether")})

    # The reward parameter in feeHistory variable contains an array of arrays.
    # each of the inner arrays has priority gas values,
    # corresponding to the given percentiles [10,20,30]
    # the number of inner arrays =
    #     the number of blocks that we gave as the parameter [5]
    # here we take each of the inner arrays and
    # sort the values in the arrays as low, medium or high,
    # based on the array index
    for feeList in feeHistory["reward"]:
        # 10 percentile values - low fees
        feeByPriority["low"].append(feeList[0])
        # 20 percentile value - medium fees
        feeByPriority["medium"].append(feeList[1])
        # 30 percentile value - high fees
        feeByPriority["high"].append(feeList[2])

    # Take each of the sorted arrays in the feeByPriority dictatory and
    # calculate the gas estimate, based on the priority level
    # which is given as the key in the feeByPriority dictatory
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
            totalGasFee = int(float(totalGasFee)* 1.01)
            # print()
            return suggestedMaxPriorityFeePerGasGwei, suggestedMaxFeePerGasGwei, totalGasFee




