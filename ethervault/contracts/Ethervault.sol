pragma solidity ^0.8.16;
// SPDX-License-Identifier:MIT
/*

888~~    d8   888                       Y88b      /                    888   d8
888___ _d88__ 888-~88e  e88~~8e  888-~\  Y88b    /    /~~~8e  888  888 888 _d88__
888     888   888  888 d888  88b 888      Y88b  /         88b 888  888 888  888
888     888   888  888 8888__888 888       Y888/     e88~-888 888  888 888  888
888     888   888  888 Y888    , 888        Y8/     C888  888 888  888 888  888
888___  "88_/ 888  888  "88___/  888         Y       "88_-888 "88_-888 888  "88_/



Darkerego, 2023 ~ Ethervault is a lightweight, gas effecient,
multisignature wallet
["0x7612E93FF157d1973D0f95Be9E4f0bdF93BAf0DE","0xE1cb8a4e283315b653D3369a09411DF32eDc60F6"]
*/
//["0x5B38Da6a701c568545dCfcB03FcB875f56beddC4","0xAb8483F64d9C6d1EcF9b849Ae677dD3315835cb2","0x4B20993Bc481177ec7E8f571ceCaE8A9e22C02db"] 50000000000000000
contract EtherVault {

    /*
      @dev: gas optimized variable packing
    */
    uint8 private mutex;
    uint8 public signerCount;
    uint8 public threshold;
    uint16 public proposalId;
    uint32 public execNonce;
    uint32 private txCount;
    uint32 private lastDay;
    uint128 public dailyLimit;
    uint128 public spentToday;


    struct Proposal{
        address proposer;
        address modifiedSigner;
        uint8 newThreshold;
        uint8 numSigners;
        uint32 initiated;
        uint128 newLimit;
        mapping (address => uint8) approvals;
    }

    struct Transaction{
        address dest;
        uint128 value;
        bytes data;
        uint8 numSigners;
        mapping (address => uint8) approvals;
    }

    /*
      @dev: Error codes:
      This is cheaper than using require statements or strings.
      Tried using bytes, but no good way to convert them to strings,
      so that leaves unsigned ints as error codes.
    */
    bytes2 aErr = "03";
    bytes2 pErr = "12";
    bytes2 tErr = "05";
    bytes2 nErr = "06";
    error FailAndRevert(bytes2);

    /*
      @dev: Error Codes are loosely modeled after HTTP error codes. Their definitions are
      here and in the documentation:

      03 -- Restricted Function Errors
          -- Access denied for caller attempting to access protected function (caller is not a signer)
          -- Access denied because state is Locked (blocked attempted reentrancy)
      04 -- Transaction Errors
          -- Cannot execute because transaction not found (either already executed or invalid txid)
          -- Insufficient balance for request
      06 -- Nonce Error
      12 Signature Errors
         -- Cannot add signer because address already is a signer
         -- Cannot sign, no proposal Found
         -- Cannot revoke because address is not a signer
         -- Cannot sign because caller already signed
         -- Cannot propose, proposal already pending

    */


    /*
      @dev: Mapping Indexes
       Signer address => 1 (substituted for bool to save gas)
       TXID > Transaction
       ProposalID => Proposal
    */
    mapping (address => uint8) isSigner;
    mapping (uint32 => Transaction) public pendingTxs;
    mapping (uint16 => Proposal) public pendingProposals;

    function auth(address s) private view {
        /*
          @dev: Checks if sender is caller
          and for reentrancy.
        */
        if( isSigner[s] == 0 || mutex == 1){
            revert FailAndRevert(aErr);
       }
    }

    function checkNonce(uint32 _nonce) private {
        if (_nonce <= execNonce){
            revert FailAndRevert(nErr);
        }
        execNonce += 1;
    }


    modifier protected {
        /*
          @dev: Restricted function access protection and reentrancy guards.
          Saves some gas by combining these checks and using an int instead of
          bool.
        */
       auth(msg.sender);
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
        uint32 txid,
        address owner
    ) private view returns(bool){
        if (pendingTxs[txid].approvals[owner] == 0){
           return false;
       }
       return true;
    }

    function alreadySignedProposal(address signer) private view {
        if (pendingProposals[proposalId].approvals[signer] == 1){
            revert FailAndRevert(pErr);
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

    function signProposal(address caller, uint16 _proposalId) private {
        pendingProposals[_proposalId].approvals[caller] = 1;
        pendingProposals[_proposalId].numSigners += 1;
    }

    function newProposal(
        address _signer,
        uint128 _limit,
        uint8 _threshold
    ) external protected returns(uint16){
        proposalId += 1;
        Proposal storage prop = pendingProposals[proposalId];
        (prop.modifiedSigner, prop.newLimit, prop.initiated,
        prop.newThreshold) = (_signer, _limit,
        uint32(block.timestamp),  _threshold);
        signProposal(msg.sender, proposalId);
        return proposalId;
    }

    function deleteProposal(uint16 _proposalId) external protected {
        /*
          @dev: Allow the proposer to delete a pending proposal.
        */
        Proposal storage proposalObj = pendingProposals[_proposalId];
        if (proposalObj.proposer == msg.sender){
            delete pendingProposals[_proposalId];
        }
    }


    function signProposal(uint16 _proposalId) external protected {
        alreadySignedProposal(msg.sender);
        Proposal storage proposalObj = pendingProposals[_proposalId];
        // if limit/threshold are being updated
        if (proposalObj.newLimit > 0||proposalObj.newThreshold >0){
            // if all signers have signed
            if(proposalObj.numSigners +1 == signerCount)  {
                dailyLimit = proposalObj.newLimit;
                threshold = proposalObj.newThreshold;
            }
        }
        // if we are adding or revoking a signer
        if (proposalObj.modifiedSigner != address(0)) {
            if(proposalObj.numSigners +1 == signerCount)  {
                /* @dev: Including this caller, all signers have been accounted for,
                    the action shall be executed now.
                */
                if (isSigner[proposalObj.modifiedSigner] == 1) {
                    /*
                    @dev: Signer exists, so this must be a revokation proposal.
                    revoke this signer and reset the approval count.
                    Admin cannot be revoked.
                    */
                    isSigner[proposalObj.modifiedSigner] = 0;
                    signerCount-=1;

                } else {
                    /*
                    @dev: Signer does not exist yet, so this must be signer addition.
                    Grant signer role, reset pending signer count.
                    */
                    isSigner[proposalObj.modifiedSigner] = 1;
                        signerCount+=1;

                  }

              }
          }
          // finally, clear storage for gas refund
          delete pendingProposals[_proposalId];
    }


    function deleteTx(
        /*
          @dev: Remove pending transaction from storage and cancel it.
        */
        uint32 txid,
        uint32 _nonce
        ) external protected {
        checkNonce(_nonce);

        if (pendingTxs[txid].dest == address(0)) {
            revert FailAndRevert(tErr);
        }
        delete pendingTxs[txid];
    }


    function approveTx(
        /*
          @dev: Function to approve a pending tx. If the signature threshold
          is met, the transaction will be executed in this same call. Reverts
          if the caller is the same signer that initialized or already approved
          the transaction.
        */
        uint32 txid,
        uint32 _nonce
        ) external protected {
        Transaction storage _tx = pendingTxs[txid];
        checkNonce(_nonce);
        if(!alreadySigned(txid, msg.sender)){
            if (_tx.dest == address(0)){
                revert FailAndRevert(tErr); // tx does not exist
            }
            if(_tx.numSigners + 1 >= threshold){
                execute(_tx.dest, _tx.value, _tx.data);
                delete pendingTxs[txid];
            } else {
                signTx(txid, msg.sender);
            }

        } else {
            revert FailAndRevert(tErr);
        }
    }

    function signTx(uint32 txid, address signer) private {
        /*
          @dev: register a transaction confirmation.
        */
        pendingTxs[txid].approvals[signer] = 1;
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
        uint32 _nonce

        ) external payable protected returns(uint32) {
        /*Nonce also is transaction Id*/
        checkNonce(_nonce);
        // gas effecient balance call
        uint128 self;
        assembly {
            self :=selfbalance()
        }

        if(self < value){
            revert FailAndRevert(tErr);
        }

        if (underLimit(value)) {
            // limit not reached
            spentToday += value;
            execute(recipient, value, data);
        } else {
            txCount += 1;
            // requires approval from signatories -- not factored into daily allowance
            Transaction storage txObject = pendingTxs[txCount];
            (txObject.dest, txObject.value, txObject.data) = (recipient, value, data);
            signTx(txCount, msg.sender);
        }
        return txCount;

    }

    function underLimit(uint128 _value) private returns (bool) {
        /*
          @dev: Function to determine whether or not a requested
          transaction's value is over the daily allowance and
          shall require additional confirmation or not. If it is
          a different day from the last time this ran, reset the
          allowance.
        */
        uint32 t = uint32(block.timestamp / 1 days);
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

     /*
       @dev: Allow arbitrary deposits to contract.
     */

     receive() external payable {}

}

