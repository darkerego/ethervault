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
is currently, it costs about 1,300,000 gas to deploy the contract with 1000 optimization runs. This is roughly just over  
the price of five dex swaps in my experience. If you wait till midnight on a saturday when gas cost is at say 20 gw, 
it's only going to cost you about 0.03 Eth in fees to deploy.  
</p>

<p>
In order to revoke or add a new signer, or change the limit or threshold, <i>all</i> current signers must approve of 
the change. This process works just like executing a transaction, and the proposed changes will be updated whenever 
the last required signer approves.
</p>

### Error Codes

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