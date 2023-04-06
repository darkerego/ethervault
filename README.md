# EtherVault (Beta)

### About
<p>
Ethervault is a multi-signature smart contract designed for storing ethereum that enforces a spending limit. 
It can also store ERC20 (and other) tokens as well. 
</p>

<p>
There are two different versions, Ethervault and EthervaultL2. Ethervault was written to be gas efficient and cheap to 
deploy above all else. EthervaultL2 is a more featured version of Ethervault which I wrote without paying much attention 
to gas efficiency or bytecode size. It is intended to be used on Layer 2 networks, which typically have much lower 
transaction fees. Ethervault (version 1) is intended to be used on main net, which generally has very high fees.
</p>


### TODO 

- Write automated tests for contract functions
- Fuzzing with echidna
- Test all of the function in EthervaultL2
  - Withdraw works 
  - SubmitRawTx works
  # TODO: test proposal functions on EthervaultL2

### Changelog 
April 5, 2023

- Finally, got around to testing out the new version. Withdrawal functionality is good. Had to fix one thing where I forgot 
  to increment spentToday value.
- Further optimized the contract.
  - rewrote withdraw() logic
  - combined the signTx and signProposal into one function
- Added the ability to pause the contract via a proposal. When the contract is paused, proposal functionality still works, 
  while withdrawals are disabled. To pause or unpause the contract, a proposal must be submitted and approved.
 
### Changelog
April 3, 2023

- Fixed the assembly call function. Now works for token transfers. NOTE: still need to test a few things, so if you deploy this, 
  make sure you test everything.

March 26/2023


- Switched execute(r,v,d) from inline assembly to regular solidity because token transfers were failing, I am 
 not entirely sure why, but it must be something with the YUL call syntax because it works fine with Solidity's call(). 

- Updated the CLI tool's gas estimation logic which required a refractor of the build_contract_interaction_tx function 
   calls.

March 24/2023

- Fixed a vulnerability with the way that the nonce logic was implemented. Previously, 
  it was possible to submit a transaction with a very high nonce, which could render the 
  entire contract unusable, trapping funds forever. Implemented a check to make sure that 
  the nonce can only ever increment by +1. 


March 13/2023

- Finished implementing all functions to the command line tool.

March 9/2023

- Upgrade status from alpha to beta
- Refactored the proposal functions eliminating 3 functions and saving about 120,000 gas in deployment
- separated nonce and txid
- changed error messages to bytes2

March 10, 2023

- Fixed a bug with the proposals
- Refractored the authentication modifer to also 
 check nonce on all protected functions

- Continued Testing functions. Confirmed working:
  - Proposal to modify signers is working
  - Proposal to update limits is working
  - Execute transaction over limit is working 
  - Execute transaction under limit is working



### EtherVault Features

<p>
- Simple to use multi-signature secure smart contract wallet.
- Designed to be gas efficient and reasonably inexpensive to deploy on Ethereum main net.
- Configurable daily spending limit (only for Ethereum).
- Larger eth withdrawals require approval from additional signers. 
- Signer accounts, required signer count for withdrawal, and daily spending limit are configured at deployment.
- Deployment costs: With optimization at 100 runs, consumes 1,339,326 gas. With a gas price of ~20gw, that's only
    0.028 eth, or at the time of this writing, $41.42 on Ethereum mainnet.
</p>

### EtherVaultL2 Features

<p>
- Simple to use multi-signature secure smart contract wallet with more features than EtherVault.
- Written without gas/deployment costs constraints.
- Configurable daily spending limit for both Ethereum and ERC20 tokens.
    - In order to limit token withdrawals, you need to first run trackToken(token_address, oracle_address), 
    supplying the token's address and the TOKEN/USD chainlink price oracle address.
    - Ethereum/USD oracle is configured at deployment.
- Withdrawals can be initiated by either calling withdraw(), or calling submitRawTx().
    - The withdraw() function will automatically encoded the calldata and 
    does not take a `data` parameter.
    - The submitRawTx() function takes parameters `recipient`, `_value`, and `data`, allowing 
     users a greater deal of flexibility. For obvious reasons, raw transactions always require 
     approval from additional signers. Note that this is NOT the case with EtherVault (version 1) 
     because version 1 only enforces spending limits for Ethereum.
- Deployment cost: With optimization at 100 runs: consumes 1,978,289 gas. At a price around 20 gw, that is about 
    0.034 eth, which right now is about $64 on Ethereum mainnet.
</p>

### Multi-Signature Logic Flow

<p>
When the contract is deployed, 3 parameters are given: a list of authorized signers, a threshold, and a daily spending limit. 
The threshold  is how many signers must approve a transaction that exceeds the daily spending limit. When a transaction 
requires approval, the amount does not count towards the daily spending limit.
</p>

<p>
<b>Important: </b> The dailyLimit value repesents a raw ethereum wei value with EtherVault. However, with EtherVaultL2, 
it represents a dollar value. Examples:
</p>

<p>
Ethervault: To allow withdrawing up to 0.025 ethereum per day, you'd use a value of `25000000000000000`. 
</p>

<p>
EtherVaultL2: To allow withdrawing up to $50 per day of Ethereum and/or tokens: you'd use a value of `50`. 
</p>

<b>
Executing Transactions
</b>
<p>

  - An authorized signer submits a transaction proposal.
  - Ethervault determines whether the requested amount is under the daily spending limit 
    - Case 1: Amount is less than or equal to spending limit, which has not been exceeded
      - Funds are sent to destination in this same transaction and no further action is required.
    - Case 2: Requested amount exceeds daily limit, or limit has already been exceeded.
      - Transaction is queued pending approval from the required number of signers ("threshold" setting)
      - Signers submit their approvals. When the last required signer approves the transaction, it will be executed in that same transaction.
      - Finally, in order to take advantage of Ethereum's gas refund, the transaction data is deleted from storage.
</p>

<b>
Changing Parameters After Deployment
</b>

<p>
I almost left all of these settings as immutable, and perhaps will create another version incase that is what someone 
is looking for, but ultimately adding this functionality did not add a tremendous amount to the deployment costs. As it 
is currently, it costs about 1,300,000 gas to deploy the contract with 1000 optimization runs. This is roughly just over  
the price of five dex swaps in my experience. If you wait till midnight on a saturday when gas cost is at say 20 gw, 
it's only going to cost you about 0.03 Eth in fees to deploy.  
</p>

<p>
In order to revoke or add a new signer, or change the limit or threshold, <i>all</i> current signers must approve of 
the change. This process works just like executing a transaction, and the proposed changes will be updated whenever 
the last required signer approves.
</p>

### Error Codes (Ethervault version 1)

<p>
In order to have the lowest possible bytecode size and thus deployment costs, many gas optimizations were implemented, 
and that includes not using strings for error statements. First, I tried bytes32, and then bytes8 in place of strings,
but there is no simple way to convert them to strings (in modern versions of solidity anyway)that would not end up 
costing even more gas than just using strings to begin with. Then I decided to use uint8's instead. But this still takes 
up a decent amount of space! Finally, I decided to forgo the variables altogether.

</p>

<pre>

contract Failure{
  function JustRevert() public pure {
    error TxError(uint16)
    revert TxError (404);
  }
}
</pre>

<p>
Alas, there are the Error code definitions.
</p>

<pre>
/*
      @dev: Error Code Glossary
      403 -- Access Denied
      404 -- TX with given id not Found
      423 -- State is Locked
      208 -- Caller already signed
      406 -- Signer does not exist 
      412 -- Address already is a signer
      302 -- No proposal Found
      204 -- Proposal already pending
*/

</pre>