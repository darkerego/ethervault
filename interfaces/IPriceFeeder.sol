// SPDX-License-Identifier:MIT

pragma solidity ^0.8.0;

interface IPriceFeeder {
    function checkFeedExists(address) external returns(bool);
    function getPrice(address tokenAddress) external returns(uint);
    function getConversionRate(address, uint) external returns(uint);
}