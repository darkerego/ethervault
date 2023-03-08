# EtherVault

### About
<p>
Ethervault is a multisignature smart contract designed for storing ethereum that enforces a spending limit. 
It can also store ERC20 (and other) tokens as well, although currently the spending limits will only apply to 
Ethereum.
</p>

### Features

<p>

- Simple to use multi-signature secure smart contract wallet.
- Designed to be gas efficient and reasonably inexpensive to deploy on Ethereum main net.
- Configurable daily spending limit.
- Larger withdrawals require approval from additional signers. 
- Signer accounts, required signer count for withdrawal, and daily spending limit are configured at deployment.
</p>

### Multi-Signature Logic Flow

<p>
When the contract is deployed, 3 parameters are given: a list of authorized signers, a threshold, and a daily spending limit. 
The threshold  is how many signers must approve a transaction that exceeds the daily spending limit. When a transaction 
requires approval, the amount does not count towards the daily spending limit.
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
is currently, it costs about 1,000,000 gas to deploy the contract. This is roughly the price of four average dex swaps 
in my experience, and at a gas price of 
</p>

<p>
In order to revoke or add a new signer, or change the limit or threshold, <i>all</i> current signers must approve of 
the change. This process works just like executing a transaction, and the proposed changes will be updated whenever 
the last required signer approves.
</p>