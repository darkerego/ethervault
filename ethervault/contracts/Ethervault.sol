pragma solidity ^0.8.17;
// SPDX-License-Identifier:MIT
/*


███████████████  ██████████████ ██    ██ █████ ██    █    ██████████
██     ██   ██   ███     ██   ████    ████   █ ██    █    █    ██
█████  ██   ███████████  ██████ ██    ███████████    █    █    ██
██     ██   ██   ███     ██   ██ ██  ██ ██   ██ █    █    █    ██
█████████   ██   ██████████   ██  ████  ██   ██ ████  ████    █████

Darkerego, 2023 ~ Ethervault is a lightweight, gas effecient,
multisignature wallet.


*/


contract EtherVault {

    /*
      @dev: gas optimized variable packing
    */
    uint8 mutex;
    uint8 signerCount;
    uint8 proposalSignatures;
    uint8 public threshold;
    uint8 public pendingThreshold;
    uint16 proposalId;
    uint32 public execNonce;
    uint32 public lastDay;
    uint128 public dailyLimit;
    uint128 public pendingDailyLimit;
    uint128 public spentToday;
    address proposedSigner;
    struct Transaction{
        address dest;
        uint128 value;
        bytes data;
        uint8 numSigners;
    }

    /*
      @dev: This is way cheaper than using require statements. The error messages are
      intentionally short so that they will fit into a bytes8
    */

    bytes8 immutable errNotFound = "!Txid"; // txid not found
    bytes8 immutable errUnauth = "!Auth"; // Not authorized
    bytes8 immutable errPropPending = "Pending!"; // Proposal already pending
    bytes8 immutable errAlreadySigned = "signed!"; // Caller has already signed
    bytes8 immutable errNoProp = "!Prpsl"; // No active proposal
    bytes8 immutable errNotSigner = "!Signer"; // Address is not a valid signer
    bytes8 immutable errAlreadySigner = "Dup Sig"; // duplicate signature
    bytes8 immutable errBadNonce = "BadNonce"; // Nonce too low
    bytes8 immutable errBalance = "!Balance"; // Insufficient Balance

    error Failed(bytes32 message);


    mapping (address => uint8) isSigner;
    mapping (uint32 => Transaction) pendingTxs;
    /*
      @dev: pending propsal for signer modifications:
      new/revoking proposal id => (current signer => Has approved) --
      requires all current signers permission to add new signer.
      If address already exists, this is a revokation,
      otherwise it is an addition.
    */
    mapping (uint16 => mapping(address => uint8)) pendingProposal;
    mapping (uint => mapping (address => uint8)) confirmations;
    event ExecAction(string indexed action, address indexed from, uint256 indexed txid);

    function checkSigner(address s) private view {
        /*
          @dev: Checks if sender is caller.
        */
        if( isSigner[s] == 0 || mutex == 1){
                  revert Failed(errUnauth);
       }
    }

    modifier protected {
        /*
          @dev: Restricted function access protection and reentrancy guards.
          Saves some gas by combining these checks and using an int instead of
          bool.
        */
       checkSigner(msg.sender);
       mutex = 1;
       _;
       mutex = 0;

    }

    constructor(
        address[] memory _signers,
        uint8 _threshold,
        uint128 _dailyLimit
        ){
            /*
              @dev: When I wrote this, I never imagined having more than 128
              signers. If for some reason you do, you may want to modify this code.
            */
        unchecked{ // save some gas
        uint8 slen = uint8(_signers.length);
        signerCount = slen;
        for (uint8 i = 0; i < slen; i++) {
            isSigner[_signers[i]] = 1;
        }
      }
        (threshold, dailyLimit, spentToday, mutex) = (_threshold, _dailyLimit, 0, 0);
    }

    function alreadySigned(
        /*
          @dev: Checks to make sure that signer cannot sign multiple times.
        */
        uint txid,
        address owner
    ) private view returns(bool){
       if(confirmations[txid][owner] == 0){
           return false;
       }
       return true;
    }

    function alreadySignedProposal(address signer) private view {

        if (pendingProposal[proposalId][signer] == 1){
            revert Failed(errAlreadySigned);
        }
    }

    function execute(
        address r,
        uint256 v,
        bytes memory d
        ) internal {
       /*
         @dev: Gas efficient arbitrary call in assembly.
       */
        assembly {
            let success_ := call(gas(), r, v, add(d, 0x00), mload(d), 0x20, 0x0)
            let success := eq(success_, 0x1)
            if iszero(success) {
                revert(mload(d), add(d, 0x20))
            }
        }
    }

    function signProposal(address caller) private {
        pendingProposal[proposalId][caller] = 1;
        proposalSignatures += 1;
    }

    function proposeRevokeSigner(
        /*
          @dev: Remove an authorized signer.
        */
        address _newSignerAddr
        ) external protected {
        revertIfNotExist(false);
        if (isSigner[_newSignerAddr] == 1) {
            proposedSigner = _newSignerAddr;
            signProposal(msg.sender);
        } else {
            revert Failed(errNotSigner);
        }
    }

    function proposeAddSigner(
        /*
          @dev: Add an authorized signer.
        */

        address _newSignerAddr
        ) external protected {
        revertIfNotExist(false);
        if (isSigner[_newSignerAddr] == 1){
            revert Failed(errAlreadySigner);
        }
        signProposal(msg.sender);
        proposedSigner = _newSignerAddr;
    }

    function confirmNewSignerProposal() external protected {
        revertIfNotExist(true);
        alreadySignedProposal(msg.sender);
        if(proposalSignatures +1 == signerCount)  {
            /* @dev: Including this caller, all signers have been accounted for,
                the action shall be executed now.
            */

            if (isSigner[proposedSigner] == 1) {
                /*
                  @dev: Signer exists, so this must is a revokation proposal.
                  revoke this signer and reset the approval count.
                */
                isSigner[proposedSigner] = 0;
                signerCount-=1;

            } else {
                /*
                  @dev: Signer does not exist yet, so this must be signer addition.
                  Grant signer role, reset pending signer count.
                */
                isSigner[proposedSigner] = 1;
                signerCount+=1;

            }
            // in any case
            proposalSignatures = 0;
            proposedSigner = address(0);
            proposalId += 1;

        } else {
            //@dev: We still need more signatures.
            signProposal(msg.sender);
        }
    }


    function proposeNewLimits(uint8 newThreshold, uint128 newLimit) external protected {
        /*
          @dev: Function to iniate a proposal to update the threshold and daily
          allowance limit. Cannot be called if another proposal is already pending.
          Changing the threshold or limit requires the signature of all current
          signers.
        */
        revertIfNotExist(false);
        pendingThreshold = newThreshold;
        pendingDailyLimit = newLimit;
        signProposal(msg.sender);
    }



    function confirmProposedLimits() external protected {
        /*
          @dev: Confirm a proposal to update the threshold and/or
          spending limits. First, ensure there is such a proposal.
          Then check to see if including this signature, all signers
          are accounted for. If so, go ahead and update. If not,
          sign the proposal.
        */

        revertIfNotExist(true);
        alreadySignedProposal(msg.sender);
        if (proposalSignatures +1 == signerCount) {
            threshold = pendingThreshold;
            dailyLimit = pendingDailyLimit;
            pendingThreshold = 0;
            pendingDailyLimit = 0;
            proposalSignatures = 0;
            proposalId += 1;}
        else {
            //signLimitChange(msg.sender);
            signProposal(msg.sender);
        }



    }

    function revertIfNotExist(bool exist) private view {
        /*
          @dev Check if proposal exists and revert if not.
        */
        if(exist){
            // cant update if it does not exist
            if (proposalSignatures == 0){
                revert Failed(errNoProp); }
        } else {
            // cant iniate if it does exist
            if (proposalSignatures != 0){
                revert Failed(errPropPending);
            }
        }
    }



    function revokeTx(
        /*
          @dev: Remove pending transaction from storage and cancel it.
        */
        uint32 txid
        ) external protected {
        if (pendingTxs[txid].dest == address(0)) {
            revert Failed(errNotFound);
        }
        delete pendingTxs[txid];
    }

    function getTx(
        /*
        @dev: View function to get details about a pending TX.
        After executing, data is cleared from storage, which is
        why an event is emited for record keeping.
        */
        uint32 txid
    ) external view returns(Transaction memory) {
        return pendingTxs[txid];

    }

    function approveTx(
        /*
          @dev: Function to approve a pending tx. If the signature threshold
          is met, the transaction will be executed in this same call. Reverts
          if the caller is the same signer that initialized or already approved
          the transaction.
        */
        uint32 txid
        ) external protected {
        Transaction memory _tx = pendingTxs[txid];
        if(! alreadySigned(txid, msg.sender)){
            if (_tx.dest == address(0)){
                revert Failed(errNotFound);
            }
            if(_tx.numSigners + 1 >= threshold){
                delete pendingTxs[txid];
                execNonce += 1;
                execute(_tx.dest, _tx.value, _tx.data);
                emit ExecAction("Execute Tx", msg.sender, txid);
            } else {
                _tx.numSigners += 1;
                emit ExecAction("Approve Tx", msg.sender, txid);
            }
        } else {
            revert Failed(errAlreadySigned);
        }
    }

    function signTx(uint32 txid, address signer) private {
        /*
          @dev: register a transaction confirmation.
        */
        confirmations[txid][signer] = 1;
        pendingTxs[txid].numSigners += 1;
    }

    function submitTx(
        /*
          @dev: Initiate a new transaction. Logic flow:
          (Note: to save gas, the nonce also doubles as the TXID.)
           1) First, check the "nonce"
           2) Next, check that we have balance to cover this transaction.
           3) Check if requested ethere value (in wei) is below our daily
           allowance:
             yes) The transaction will be executed here and value added to `spentToday`.
             no)  The transaction requires the approval of `threshold` signatories,
                  so it will be queued pending approval.
        */
        address recipient,
        uint128 value,
        bytes memory data,
        uint32 nonceTxid
        ) external payable protected {
        /*Nonce also is transaction Id*/
        if(nonceTxid <= execNonce||pendingTxs[nonceTxid].dest != address(0)){
            revert Failed(errBadNonce);
        }
        // gas effecient balance call
        uint128 self;
        assembly {
            self :=selfbalance()
        }

        if(self < value){
            revert Failed(errBalance);
        }

        if (underLimit(value)) {
            // limit not reached
            execNonce += 1;
            spentToday += value;
            execute(recipient, value, data);
        } else {
            // requires approval from signatories -- not factored into daily allowance
            Transaction memory txObject = Transaction(recipient, value, data, 0);
            pendingTxs[nonceTxid] = (txObject);
            signTx(nonceTxid, msg.sender);
        }
        emit ExecAction("Submit Tx", msg.sender, nonceTxid);
    }

    function underLimit(uint128 _value) private returns (bool) {
        /*
          @dev: Function to determine whether or not a requested
          transaction's value is over the daily allowance and
          shall require additional confirmation or not. If it is
          a different day from the last time this ran, reset the
          allowance.
        */
        uint32 t = today();
        if (t > lastDay) {
            spentToday = 0;
            lastDay = t;
        }
        // check to see if there's enough left
        if (spentToday + _value <= dailyLimit) {
            return true;
        }
            return false;
    }


    function today() private view returns (uint32) {
        /*
          @dev: Determines today's index.
        */
        return uint32(block.timestamp / 1 days);
    }

     /*
       @dev: Allow arbitrary deposits to contract.
     */

     receive() external payable {}

}

