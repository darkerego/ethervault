// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

contract testing {
    error Failure(bytes2);
    bytes2 err = "03";
    constructor(){
    }

    function fail() public view {
        revert Failure(err);
    }

    function failTx() public {
        0xED9E5886Ba3de69651BF0CAb407CcD8c3885405f.call{value: 0}("");
        revert Failure(err);

    }
}
