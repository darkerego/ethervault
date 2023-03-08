#### Slither Report

<p>
This document is a list of the "issues" identified by Slither and the reasons why I did not "fix" them.
</p>


#### Report

<p>
This is a false positive, the contract does have withdraw functionality.
</p>

<pre>
Contract locking ether found:
        Contract EtherVault (ethervault/contracts/Ethervault.sol#19-410) has payable functions:
         - EtherVault.submitTx(address,uint128,bytes,uint32) (ethervault/contracts/Ethervault.sol#339-382)
         - EtherVault.receive() (ethervault/contracts/Ethervault.sol#408)
        But does not have a function to withdraw the ether
Reference: https://github.com/crytic/slither/wiki/Detector-Documentation#contracts-that-lock-ether

</pre>


<p>
Events consume far too much gas to be useful in this case. The blockchain is immutable, and that will suffice.
</p>
<pre>
EtherVault.submitTx(address,uint128,bytes,uint32) (ethervault/contracts/Ethervault.sol#339-382) should emit an event for: 
        - spentToday += value (ethervault/contracts/Ethervault.sol#373) 
Reference: https://github.com/crytic/slither/wiki/Detector-Documentation#missing-events-arithmetic
</pre>

<p>
I don't think this is an issue because a miner could not manipulate time by more than 15-30 minutes AFAIK, and we are 
operating in intervals of 24 hours in this contract.
</p>

<pre>
EtherVault.underLimit(uint128) (ethervault/contracts/Ethervault.sol#384-402) uses timestamp for comparisons
        Dangerous comparisons:
        - t > lastDay (ethervault/contracts/Ethervault.sol#393)
Reference: https://github.com/crytic/slither/wiki/Detector-Documentation#block-timestamp
</pre>

<p>
I simply disagree that using assembly is a risk.
</p>


<pre>
EtherVault.execute(address,uint256,bytes) (ethervault/contracts/Ethervault.sol#146-161) uses assembly
        - INLINE ASM (ethervault/contracts/Ethervault.sol#154-160)
EtherVault.submitTx(address,uint128,bytes,uint32) (ethervault/contracts/Ethervault.sol#339-382) uses assembly
        - INLINE ASM (ethervault/contracts/Ethervault.sol#362-364)
Reference: https://github.com/crytic/slither/wiki/Detector-Documentation#assembly-usage
</pre>

