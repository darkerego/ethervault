import json

vault_abi = json.loads("""[
	{
		"inputs": [
			{
				"internalType": "address[]",
				"name": "_signers",
				"type": "address[]"
			},
			{
				"internalType": "uint8",
				"name": "_threshold",
				"type": "uint8"
			},
			{
				"internalType": "uint128",
				"name": "_dailyLimit",
				"type": "uint128"
			}
		],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"inputs": [
			{
				"internalType": "bytes2",
				"name": "",
				"type": "bytes2"
			}
		],
		"name": "FailAndRevert",
		"type": "error"
	},
	{
		"inputs": [
			{
				"internalType": "uint16",
				"name": "_proposalId",
				"type": "uint16"
			},
			{
				"internalType": "uint32",
				"name": "_nonce",
				"type": "uint32"
			}
		],
		"name": "approveProposal",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint32",
				"name": "txid",
				"type": "uint32"
			},
			{
				"internalType": "uint32",
				"name": "_nonce",
				"type": "uint32"
			}
		],
		"name": "approveTx",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "dailyLimit",
		"outputs": [
			{
				"internalType": "uint128",
				"name": "",
				"type": "uint128"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint16",
				"name": "_proposalId",
				"type": "uint16"
			},
			{
				"internalType": "uint32",
				"name": "_nonce",
				"type": "uint32"
			}
		],
		"name": "deleteProposal",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint32",
				"name": "txid",
				"type": "uint32"
			},
			{
				"internalType": "uint32",
				"name": "_nonce",
				"type": "uint32"
			}
		],
		"name": "deleteTx",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "execNonce",
		"outputs": [
			{
				"internalType": "uint32",
				"name": "",
				"type": "uint32"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_signer",
				"type": "address"
			},
			{
				"internalType": "uint128",
				"name": "_limit",
				"type": "uint128"
			},
			{
				"internalType": "uint8",
				"name": "_threshold",
				"type": "uint8"
			},
			{
				"internalType": "uint32",
				"name": "_nonce",
				"type": "uint32"
			}
		],
		"name": "newProposal",
		"outputs": [
			{
				"internalType": "uint16",
				"name": "",
				"type": "uint16"
			}
		],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint16",
				"name": "",
				"type": "uint16"
			}
		],
		"name": "pendingProposals",
		"outputs": [
			{
				"internalType": "address",
				"name": "proposer",
				"type": "address"
			},
			{
				"internalType": "address",
				"name": "modifiedSigner",
				"type": "address"
			},
			{
				"internalType": "uint8",
				"name": "newThreshold",
				"type": "uint8"
			},
			{
				"internalType": "uint8",
				"name": "numSigners",
				"type": "uint8"
			},
			{
				"internalType": "uint32",
				"name": "initiated",
				"type": "uint32"
			},
			{
				"internalType": "uint128",
				"name": "newLimit",
				"type": "uint128"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint32",
				"name": "",
				"type": "uint32"
			}
		],
		"name": "pendingTxs",
		"outputs": [
			{
				"internalType": "address",
				"name": "dest",
				"type": "address"
			},
			{
				"internalType": "uint128",
				"name": "value",
				"type": "uint128"
			},
			{
				"internalType": "bytes",
				"name": "data",
				"type": "bytes"
			},
			{
				"internalType": "uint8",
				"name": "numSigners",
				"type": "uint8"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "proposalId",
		"outputs": [
			{
				"internalType": "uint16",
				"name": "",
				"type": "uint16"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "signerCount",
		"outputs": [
			{
				"internalType": "uint8",
				"name": "",
				"type": "uint8"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "spentToday",
		"outputs": [
			{
				"internalType": "uint128",
				"name": "",
				"type": "uint128"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "recipient",
				"type": "address"
			},
			{
				"internalType": "uint128",
				"name": "value",
				"type": "uint128"
			},
			{
				"internalType": "bytes",
				"name": "data",
				"type": "bytes"
			},
			{
				"internalType": "uint32",
				"name": "_nonce",
				"type": "uint32"
			}
		],
		"name": "submitTx",
		"outputs": [
			{
				"internalType": "uint32",
				"name": "",
				"type": "uint32"
			}
		],
		"stateMutability": "payable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "threshold",
		"outputs": [
			{
				"internalType": "uint8",
				"name": "",
				"type": "uint8"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"stateMutability": "payable",
		"type": "receive"
	}
]""")