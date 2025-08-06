from web3 import Web3
from dotenv import load_dotenv
import asyncio
import random
import time
import sys
import os
import json
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configuration files
CONFIG_FILE = "satsuma_config.json"
MAIN_CONFIG_FILE = "config.json"

# Terminal Colors
class Colors:
    RESET = '\033[0m'
    CYAN = '\033[36m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    WHITE = '\033[37m'
    BOLD = '\033[1m'
    PURPLE = '\033[35m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_WHITE = '\033[97m'

class Logger:
    @staticmethod
    def info(msg):
        print(f"{Colors.GREEN}[✓] {msg}{Colors.RESET}")

    @staticmethod
    def warn(msg):
        print(f"{Colors.YELLOW}[!] {msg}{Colors.RESET}")

    @staticmethod
    def error(msg):
        print(f"{Colors.RED}[✗] {msg}{Colors.RESET}")

    @staticmethod
    def success(msg):
        print(f"{Colors.GREEN}[+] {msg}{Colors.RESET}")

    @staticmethod
    def processing(msg):
        print(f"{Colors.CYAN}[⟳] {msg}{Colors.RESET}")

    @staticmethod
    def step(msg):
        print(f"{Colors.WHITE}[➤] {msg}{Colors.RESET}")

log = Logger()

# Contract ABIs
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]

SWAP_ROUTER_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "_factory", "type": "address"}, {"internalType": "address", "name": "_WNativeToken", "type": "address"}, {"internalType": "address", "name": "_poolDeployer", "type": "address"}],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {"inputs": [], "name": "WNativeToken", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "int256", "name": "amount0Delta", "type": "int256"}, {"internalType": "int256", "name": "amount1Delta", "type": "int256"}, {"internalType": "bytes", "name": "_data", "type": "bytes"}], "name": "algebraSwapCallback", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"components": [{"internalType": "bytes", "name": "path", "type": "bytes"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}, {"internalType": "uint256", "name": "amountIn", "type": "uint256"}, {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"}], "internalType": "struct ISwapRouter.ExactInputParams", "name": "params", "type": "tuple"}], "name": "exactInput", "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"components": [{"internalType": "address", "name": "tokenIn", "type": "address"}, {"internalType": "address", "name": "tokenOut", "type": "address"}, {"internalType": "address", "name": "deployer", "type": "address"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}, {"internalType": "uint256", "name": "amountIn", "type": "uint256"}, {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"}, {"internalType": "uint160", "name": "limitSqrtPrice", "type": "uint160"}], "internalType": "struct ISwapRouter.ExactInputSingleParams", "name": "params", "type": "tuple"}], "name": "exactInputSingle", "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"components": [{"internalType": "address", "name": "tokenIn", "type": "address"}, {"internalType": "address", "name": "tokenOut", "type": "address"}, {"internalType": "address", "name": "deployer", "type": "address"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}, {"internalType": "uint256", "name": "amountIn", "type": "uint256"}, {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"}, {"internalType": "uint160", "name": "limitSqrtPrice", "type": "uint160"}], "internalType": "struct ISwapRouter.ExactInputSingleParams", "name": "params", "type": "tuple"}], "name": "exactInputSingleSupportingFeeOnTransferTokens", "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"components": [{"internalType": "bytes", "name": "path", "type": "bytes"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}, {"internalType": "uint256", "name": "amountOut", "type": "uint256"}, {"internalType": "uint256", "name": "amountInMaximum", "type": "uint256"}], "internalType": "struct ISwapRouter.ExactOutputParams", "name": "params", "type": "tuple"}], "name": "exactOutput", "outputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"components": [{"internalType": "address", "name": "tokenIn", "type": "address"}, {"internalType": "address", "name": "tokenOut", "type": "address"}, {"internalType": "address", "name": "deployer", "type": "address"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}, {"internalType": "uint256", "name": "amountOut", "type": "uint256"}, {"internalType": "uint256", "name": "amountInMaximum", "type": "uint256"}, {"internalType": "uint160", "name": "limitSqrtPrice", "type": "uint160"}], "internalType": "struct ISwapRouter.ExactOutputSingleParams", "name": "params", "type": "tuple"}], "name": "exactOutputSingle", "outputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [], "name": "factory", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "bytes[]", "name": "data", "type": "bytes[]"}], "name": "multicall", "outputs": [{"internalType": "bytes[]", "name": "results", "type": "bytes[]"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [], "name": "poolDeployer", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "refundNativeToken", "outputs": [], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "token", "type": "address"}, {"internalType": "uint256", "name": "value", "type": "uint256"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}, {"internalType": "uint8", "name": "v", "type": "uint8"}, {"internalType": "bytes32", "name": "r", "type": "bytes32"}, {"internalType": "bytes32", "name": "s", "type": "bytes32"}], "name": "selfPermit", "outputs": [], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "token", "type": "address"}, {"internalType": "uint256", "name": "nonce", "type": "uint256"}, {"internalType": "uint256", "name": "expiry", "type": "uint256"}, {"internalType": "uint8", "name": "v", "type": "uint8"}, {"internalType": "bytes32", "name": "r", "type": "bytes32"}, {"internalType": "bytes32", "name": "s", "type": "bytes32"}], "name": "selfPermitAllowed", "outputs": [], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "token", "type": "address"}, {"internalType": "uint256", "name": "nonce", "type": "uint256"}, {"internalType": "uint256", "name": "expiry", "type": "uint256"}, {"internalType": "uint8", "name": "v", "type": "uint8"}, {"internalType": "bytes32", "name": "r", "type": "bytes32"}, {"internalType": "bytes32", "name": "s", "type": "bytes32"}], "name": "selfPermitAllowedIfNecessary", "outputs": [], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "token", "type": "address"}, {"internalType": "uint256", "name": "value", "type": "uint256"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}, {"internalType": "uint8", "name": "v", "type": "uint8"}, {"internalType": "bytes32", "name": "r", "type": "bytes32"}, {"internalType": "bytes32", "name": "s", "type": "bytes32"}], "name": "selfPermitIfNecessary", "outputs": [], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "token", "type": "address"}, {"internalType": "uint256", "name": "amountMinimum", "type": "uint256"}, {"internalType": "address", "name": "recipient", "type": "address"}], "name": "sweepToken", "outputs": [], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "token", "type": "address"}, {"internalType": "uint256", "name": "amountMinimum", "type": "uint256"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "feeBips", "type": "uint256"}, {"internalType": "address", "name": "feeRecipient", "type": "address"}], "name": "sweepTokenWithFee", "outputs": [], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "amountMinimum", "type": "uint256"}, {"internalType": "address", "name": "recipient", "type": "address"}], "name": "unwrapWNativeToken", "outputs": [], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "amountMinimum", "type": "uint256"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "feeBips", "type": "uint256"}, {"internalType": "address", "name": "feeRecipient", "type": "address"}], "name": "unwrapWNativeTokenWithFee", "outputs": [], "stateMutability": "payable", "type": "function"},
    {"stateMutability": "payable", "type": "receive"}
]

LIQUIDITY_ROUTER_ABI = [
    {
        "inputs": [
            {"name": "tokenA", "type": "address"},
            {"name": "tokenB", "type": "address"},
            {"name": "deployer", "type": "address"},
            {"name": "recipient", "type": "address"},
            {"name": "amountADesired", "type": "uint256"},
            {"name": "amountBDesired", "type": "uint256"},
            {"name": "amountAMin", "type": "uint256"},
            {"name": "amountBMin", "type": "uint256"},
            {"name": "deadline", "type": "uint256"}
        ],
        "name": "addLiquidity",
        "outputs": [
            {"name": "amountA", "type": "uint256"},
            {"name": "amountB", "type": "uint256"},
            {"name": "liquidity", "type": "uint128"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

VOTING_ABI = [
    {
        "name": "vote",
        "inputs": [
            {"name": "gauge_addr", "type": "address"},
            {"name": "weight", "type": "uint256"}
        ],
        "outputs": [],
        "type": "function"
    }
]

# Note: The veSUMA contract likely requires a specific lock period to end before 'exit' can be called.
# The `exit` function has a selector of `0x7f8661a1` and takes no parameters.
# The `create_lock` function has a selector of `0x12e82674` and takes `_value` and `_unlock_time` as parameters.
# We will use these selectors to manually build transactions, which is more reliable than a generic ABI.

class SatsumaBot:
    def __init__(self):
        self.config = self.load_config()
        self.w3 = self.initialize_provider()
        self.private_keys = self.get_private_keys()
        self.settings = self.load_user_settings()
        self.transaction_history = []

    def load_config(self):
        config = {
            "rpc": "https://rpc.testnet.citrea.xyz",
            "chain_id": 5115,
            "symbol": "cBTC",
            "explorer": "https://explorer.testnet.citrea.xyz",
            "swap_router": Web3.to_checksum_address("0x3012e9049d05b4b5369d690114d5a5861ebb85cb"),
            "liquidity_router": Web3.to_checksum_address("0x55a4669cd6895EA25C174F13E1b49d69B4481704"),
            "pool_address": Web3.to_checksum_address("0x080c376e6aB309fF1a861e1c3F91F27b8D4f1443"),
            "usdc_address": Web3.to_checksum_address("0x2C8abD2A528D19AFc33d2eBA507c0F405c131335"),
            "wcbtc_address": Web3.to_checksum_address("0x8d0c9d1c17ae5e40fff9be350f57840e9e66cd93"),
            "suma_address": Web3.to_checksum_address("0xdE4251dd68e1aD5865b14Dd527E54018767Af58a"),
            "vesuma_address": Web3.to_checksum_address("0x97a4f684620D578312Dc9fFBc4b0EbD8E804ab4a"),
            "voting_contract": Web3.to_checksum_address("0x1234567890123456789012345678901234567891"),
            "staking_contract": Web3.to_checksum_address("0x1234567890123456789012345678901234567892"),
            "gauge_address": Web3.to_checksum_address("0x1234567890123456789012345678901234567893")
        }
        
        try:
            with open(MAIN_CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            log.warn(f"Could not save config file: {str(e)}")
        
        return config

    def initialize_provider(self):
        try:
            w3 = Web3(Web3.HTTPProvider(self.config["rpc"]))
            if not w3.is_connected():
                raise Exception("Failed to connect to RPC")
            
            log.success(f"Connected to {self.config['rpc']}")
            log.info(f"Chain ID: {self.config['chain_id']}")
            return w3
        except Exception as e:
            log.error(f"Provider initialization failed: {str(e)}")
            sys.exit(1)

    def get_private_keys(self):
        private_keys = []
        key = os.getenv("PRIVATE_KEY_1")
        
        if not key or key == "your_private_key_here":
            log.error("No valid private key found in environment variables")
            log.info("Please set PRIVATE_KEY_1 in your .env file with your actual private key")
            
            key = input("Enter your private key (without 0x prefix): ")
            if not key:
                sys.exit(1)
        
        try:
            account = Web3().eth.account.from_key(key)
            log.success(f"Loaded private key for address: {account.address}")
            private_keys.append(key)
        except Exception as e:
            log.error(f"Invalid private key: {str(e)}")
            sys.exit(1)
        
        return private_keys

    def load_user_settings(self):
        user_settings = {
            "transaction_count": 0,
            "current_round": 0,
            "total_transactions": 0,
            "successful_transactions": 0,
            "failed_transactions": 0,
            "last_transaction_time": None
        }
        
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    user_settings.update(data)
                    log.success(f"Loaded configuration: {user_settings['transaction_count']} transactions planned")
        except Exception as e:
            log.error(f"Failed to load settings: {str(e)}")
        
        return user_settings

    def save_user_settings(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.settings, f, indent=2)
            log.success("Configuration saved successfully")
        except Exception as e:
            log.error(f"Failed to save settings: {str(e)}")

    def generate_random_amount(self):
        min_amount = 0.0001
        max_amount = 0.0002
        random_amount = random.uniform(min_amount, max_amount)
        return round(random_amount, 6)

    async def approve_token(self, account, token_address, spender_address, amount, nonce):
        try:
            token_contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
            
            log.processing(f"Checking allowance for {token_address}")
            
            allowance = token_contract.functions.allowance(account.address, spender_address).call()
            if allowance >= amount:
                log.success("Sufficient allowance already exists")
                return {"success": True, "nonce": nonce}
            
            log.processing("Sending approval transaction...")
            
            approve_tx = token_contract.functions.approve(spender_address, amount).build_transaction({
                "from": account.address,
                "gas": 100000,
                "gasPrice": self.w3.eth.gas_price,
                "nonce": nonce
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(approve_tx, private_key=account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            log.processing("Waiting for approval confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt["status"] == 1:
                log.success(f"Approval successful! Tx: {self.config['explorer']}/tx/{tx_hash.hex()}")
                return {"success": True, "nonce": nonce + 1}
            else:
                log.error("Approval transaction failed")
                return {"success": False, "nonce": nonce}
                
        except Exception as e:
            log.error(f"Approval error: {str(e)}")
            return {"success": False, "nonce": nonce}

    async def get_token_balance(self, token_address, account_address):
        try:
            token_contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
            balance = token_contract.functions.balanceOf(account_address).call()
            decimals = token_contract.functions.decimals().call()
            symbol = token_contract.functions.symbol().call()
            
            return {
                "balance": balance,
                "decimals": decimals,
                "symbol": symbol,
                "formatted": balance / (10 ** decimals)
            }
        except Exception as e:
            log.error(f"Error getting token balance: {str(e)}")
            return None

    async def perform_swap(self, private_key, token_in, token_out, amount_in):
        try:
            account = self.w3.eth.account.from_key(private_key)
            log.info(f"Performing swap for {account.address}")
            
            token_in_info = await self.get_token_balance(token_in, account.address)
            if not token_in_info:
                return {"success": False, "error": "Could not get token in info"}

            amount_in_wei = int(amount_in * (10 ** token_in_info['decimals']))
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            # --- Approve first ---
            approval_result = await self.approve_token(account, token_in, self.config["swap_router"], amount_in_wei, nonce)
            if not approval_result["success"]:
                return {"success": False, "error": "Approval failed"}
            
            nonce = approval_result["nonce"]
            
            # --- Perform swap via multicall ---
            swap_router_contract = self.w3.eth.contract(address=self.config["swap_router"], abi=SWAP_ROUTER_ABI)
            deadline = int(time.time()) + 300
            
            swap_params = {
                "tokenIn": token_in,
                "tokenOut": token_out,
                "deployer": self.w3.to_checksum_address("0x0000000000000000000000000000000000000000"),
                "recipient": account.address,
                "deadline": deadline,
                "amountIn": amount_in_wei,
                "amountOutMinimum": 0,
                "limitSqrtPrice": 0
            }
            
            encoded_swap_call = swap_router_contract.functions.exactInputSingle(swap_params)._encode_transaction_data()
            
            multicall_tx = swap_router_contract.functions.multicall([encoded_swap_call]).build_transaction({
                "from": account.address,
                "gas": 500000, # Increased gas limit
                "gasPrice": self.w3.eth.gas_price,
                "nonce": nonce
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(multicall_tx, private_key=private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            log.processing("Waiting for multicall swap confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt["status"] == 1:
                log.success(f"Swap successful via multicall! Tx: {self.config['explorer']}/tx/{tx_hash.hex()}")
                self.transaction_history.append({
                    "type": "multicall_swap",
                    "tx_hash": tx_hash.hex(),
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                })
                return {"success": True, "tx_hash": tx_hash.hex()}
            else:
                log.error("Multicall swap transaction failed")
                return {"success": False, "error": "Transaction failed"}
                
        except Exception as e:
            log.error(f"Multicall swap error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def add_liquidity(self, private_key, token_a, token_b, amount_a, amount_b):
        try:
            account = self.w3.eth.account.from_key(private_key)
            log.info(f"Adding liquidity for {account.address}")
            
            amount_a_wei = int(amount_a * 10**18)
            amount_b_wei = int(amount_b * 10**18)
            nonce = self.w3.eth.get_transaction_count(account.address)

            # Approve both tokens
            approval_a = await self.approve_token(account, token_a, self.config["liquidity_router"], amount_a_wei, nonce)
            if not approval_a["success"]:
                return {"success": False, "error": "Token A approval failed"}
            nonce = approval_a['nonce']

            approval_b = await self.approve_token(account, token_b, self.config["liquidity_router"], amount_b_wei, nonce)
            if not approval_b["success"]:
                return {"success": False, "error": "Token B approval failed"}
            nonce = approval_b['nonce']
            
            # Add liquidity
            liquidity_contract = self.w3.eth.contract(address=self.config["liquidity_router"], abi=LIQUIDITY_ROUTER_ABI)
            deadline = int(time.time()) + 300
            
            liquidity_tx = liquidity_contract.functions.addLiquidity(
                token_a, token_b, account.address, account.address,
                amount_a_wei, amount_b_wei, 0, 0, deadline
            ).build_transaction({
                "from": account.address,
                "gas": 500000, # Increased gas limit
                "gasPrice": self.w3.eth.gas_price,
                "nonce": nonce
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(liquidity_tx, private_key=private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            log.processing("Waiting for liquidity confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt["status"] == 1:
                log.success(f"Liquidity added successfully! Tx: {self.config['explorer']}/tx/{tx_hash.hex()}")
                self.transaction_history.append({
                    "type": "liquidity",
                    "tx_hash": tx_hash.hex(),
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                })
                return {"success": True, "tx_hash": tx_hash.hex()}
            else:
                log.error("Liquidity transaction failed")
                return {"success": False, "error": "Transaction failed"}
                
        except Exception as e:
            log.error(f"Liquidity error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def convert_to_vesuma(self, private_key, amount, lock_time_days):
        try:
            account = self.w3.eth.account.from_key(private_key)
            log.info(f"Converting SUMA to veSUMA for {account.address}")
            
            # Use decimals for SUMA token, assuming 18
            amount_wei = int(amount * 10**18)
            unlock_time = int(time.time()) + (lock_time_days * 24 * 60 * 60)
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            # --- STEP 1: Approve SUMA token ---
            log.processing("Sending SUMA approval transaction...")
            approve_result = await self.approve_token(account, self.config["suma_address"], self.config["vesuma_address"], amount_wei, nonce)
            
            if not approve_result["success"]:
                log.error("SUMA approval failed")
                return {"success": False, "error": "Approval transaction failed"}
            
            nonce = approve_result["nonce"]
            
            # --- STEP 2: Manually build and send the create_lock transaction using the specified selector ---
            log.processing("Manually building and sending veSUMA conversion transaction...")
            
            # Selector for `create_lock` function
            selector = "0x12e82674"
            
            # Correcting the ABI encoding method
            encoded_params = self.w3.abi.encode(['uint256', 'uint256'], [amount_wei, unlock_time])
            
            # Combine the selector and the encoded parameters
            tx_data = selector + self.w3.to_hex(encoded_params)[2:]
            
            create_lock_tx = {
                "from": account.address,
                "to": self.config["vesuma_address"],
                "gas": 500000, # Increased gas limit
                "gasPrice": self.w3.eth.gas_price,
                "nonce": nonce,
                "data": tx_data
            }
            
            signed_tx = self.w3.eth.account.sign_transaction(create_lock_tx, private_key=private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            log.processing("Waiting for veSUMA conversion confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt["status"] == 1:
                log.success(f"veSUMA conversion successful! Tx: {self.config['explorer']}/tx/{tx_hash.hex()}")
                self.transaction_history.append({
                    "type": "vesuma_conversion",
                    "tx_hash": tx_hash.hex(),
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                })
                return {"success": True, "tx_hash": tx_hash.hex()}
            else:
                log.error("veSUMA conversion failed")
                return {"success": False, "error": "Transaction failed"}
                
        except Exception as e:
            log.error(f"veSUMA conversion error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def convert_vesuma_to_suma(self, private_key):
        try:
            account = self.w3.eth.account.from_key(private_key)
            log.info(f"Converting veSUMA to SUMA for {account.address}")
            
            # The selector for 'exit' is specified by the user as 0x7f8661a1
            # Note: This transaction will likely fail if the lock period has not expired.
            selector = "0x7f8661a1"
            tx_data = selector
            
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            exit_tx = {
                "from": account.address,
                "to": self.config["vesuma_address"],
                "gas": 500000, # Increased gas limit
                "gasPrice": self.w3.eth.gas_price,
                "nonce": nonce,
                "data": tx_data
            }
            
            signed_tx = self.w3.eth.account.sign_transaction(exit_tx, private_key=private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            log.processing("Waiting for veSUMA -> SUMA conversion confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt["status"] == 1:
                log.success(f"veSUMA -> SUMA conversion successful! Tx: {self.config['explorer']}/tx/{tx_hash.hex()}")
                self.transaction_history.append({
                    "type": "vesuma_to_suma_conversion",
                    "tx_hash": tx_hash.hex(),
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                })
                return {"success": True, "tx_hash": tx_hash.hex()}
            else:
                log.error("veSUMA -> SUMA conversion failed: Transaction reverted, likely due to unexpired lock period.")
                return {"success": False, "error": "Transaction failed, unexpired lock period"}
                
        except Exception as e:
            log.error(f"veSUMA -> SUMA conversion error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def stake_vesuma(self, private_key, amount):
        try:
            account = self.w3.eth.account.from_key(private_key)
            log.info(f"Staking veSUMA for {account.address}")
            
            amount_wei = int(amount * 10**18)
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            # Manually build stake transaction using selector
            # Stake selector: `0xb6b55f25` (stake(uint256))
            selector = "0xb6b55f25"
            encoded_params = self.w3.abi.encode(['uint256'], [amount_wei])
            tx_data = selector + self.w3.to_hex(encoded_params)[2:]
            
            stake_tx = {
                "from": account.address,
                "to": self.config["staking_contract"],
                "gas": 500000,
                "gasPrice": self.w3.eth.gas_price,
                "nonce": nonce,
                "data": tx_data
            }
            
            signed_tx = self.w3.eth.account.sign_transaction(stake_tx, private_key=private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            log.processing("Waiting for staking confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt["status"] == 1:
                log.success(f"veSUMA staking successful! Tx: {self.config['explorer']}/tx/{tx_hash.hex()}")
                self.transaction_history.append({
                    "type": "staking",
                    "tx_hash": tx_hash.hex(),
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                })
                return {"success": True, "tx_hash": tx_hash.hex()}
            else:
                log.error("Staking transaction failed")
                return {"success": False, "error": "Transaction failed"}
                
        except Exception as e:
            log.error(f"Staking error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def vote_with_vesuma(self, private_key, gauge_address, weight):
        try:
            account = self.w3.eth.account.from_key(private_key)
            log.info(f"Voting with veSUMA for {account.address}")
            
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            voting_contract = self.w3.eth.contract(address=self.config["voting_contract"], abi=VOTING_ABI)
            
            vote_tx = voting_contract.functions.vote(gauge_address, weight).build_transaction({
                "from": account.address,
                "gas": 200000,
                "gasPrice": self.w3.eth.gas_price,
                "nonce": nonce
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(vote_tx, private_key=private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            log.processing("Waiting for voting confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt["status"] == 1:
                log.success(f"Voting successful! Tx: {self.config['explorer']}/tx/{tx_hash.hex()}")
                self.transaction_history.append({
                    "type": "voting",
                    "tx_hash": tx_hash.hex(),
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                })
                return {"success": True, "tx_hash": tx_hash.hex()}
            else:
                log.error("Voting transaction failed")
                return {"success": False, "error": "Transaction failed"}
                
        except Exception as e:
            log.error(f"Voting error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def start_automated_swaps(self):
        if self.settings["transaction_count"] == 0:
            log.error("No transactions configured. Please set transaction count first.")
            return
        
        log.info(f"Starting automated swaps with {self.settings['transaction_count']} transactions")
        
        tokens = [self.config["usdc_address"], self.config["wcbtc_address"]]
        
        for i in range(self.settings["transaction_count"]):
            try:
                token_in = random.choice(tokens)
                token_out = random.choice([t for t in tokens if t != token_in])
                amount = self.generate_random_amount()
                private_key = random.choice(self.private_keys)
                
                log.info(f"Transaction {i+1}/{self.settings['transaction_count']}")
                
                result = await self.perform_swap(private_key, token_in, token_out, amount)
                
                if result["success"]:
                    self.settings["successful_transactions"] += 1
                    log.success(f"Swap {i+1} completed successfully")
                else:
                    self.settings["failed_transactions"] += 1
                    log.error(f"Swap {i+1} failed: {result.get('error', 'Unknown error')}")
                
                self.settings["total_transactions"] += 1
                self.settings["last_transaction_time"] = datetime.now().isoformat()
                self.save_user_settings()
                
                delay = random.uniform(5, 15)
                log.info(f"Waiting {delay:.1f} seconds before next transaction...")
                await asyncio.sleep(delay)
                
            except Exception as e:
                log.error(f"Error in transaction {i+1}: {str(e)}")
                self.settings["failed_transactions"] += 1
                self.settings["total_transactions"] += 1
                self.save_user_settings()
                continue
        
        log.success("Automated swaps completed!")
        log.info(f"Total: {self.settings['total_transactions']}, Success: {self.settings['successful_transactions']}, Failed: {self.settings['failed_transactions']}")

    def display_welcome_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        now = datetime.now()
        print(f"{Colors.BRIGHT_GREEN}{Colors.BOLD}")
        print("  ╔══════════════════════════════════════╗")
        print("  ║            S A T S U M A             ║")
        print("  ║                                      ║")
        print(f"  ║      {Colors.YELLOW}{now.strftime('%H:%M:%S %d.%m.%Y')}{Colors.BRIGHT_GREEN}            ║")
        print("  ║                                      ║")
        print("  ║      CITREA TESTNET AUTOMATION       ║")
        print(f"  ║   {Colors.BRIGHT_WHITE}ZonaAirdrop{Colors.BRIGHT_GREEN}  |  t.me/ZonaAirdr0p    ║")
        print("  ╚══════════════════════════════════════╝")
        print(f"{Colors.RESET}")

    def display_menu(self):
        print(f"\n{Colors.YELLOW}=== Satsuma DeFi Bot Menu ==={Colors.RESET}")
        print(f"{Colors.YELLOW}1. Start Automated Swaps{Colors.RESET}")
        print(f"{Colors.YELLOW}2. Set Transaction Count{Colors.RESET}")
        print(f"{Colors.YELLOW}3. Manual Swap{Colors.RESET}")
        print(f"{Colors.YELLOW}4. Add Liquidity{Colors.RESET}")
        print(f"{Colors.YELLOW}5. Convert SUMA to veSUMA{Colors.RESET}")
        print(f"{Colors.YELLOW}6. Convert veSUMA to SUMA{Colors.RESET}")
        print(f"{Colors.YELLOW}7. Stake veSUMA{Colors.RESET}")
        print(f"{Colors.YELLOW}8. Vote with veSUMA{Colors.RESET}")
        print(f"{Colors.YELLOW}9. Show Balances{Colors.RESET}")
        print(f"{Colors.YELLOW}10. Transaction History{Colors.RESET}")
        print(f"{Colors.YELLOW}11. Exit{Colors.RESET}")
        print(f"{Colors.YELLOW}{'='*35}{Colors.RESET}")

    async def show_balances(self):
        try:
            account = self.w3.eth.account.from_key(self.private_keys[0])
            log.info(f"Showing balances for {account.address}")
            
            eth_balance = self.w3.eth.get_balance(account.address)
            eth_formatted = self.w3.from_wei(eth_balance, 'ether')
            
            print(f"\n{Colors.CYAN}=== Account Balances ==={Colors.RESET}")
            print(f"{Colors.WHITE}Address: {account.address}{Colors.RESET}")
            print(f"{Colors.GREEN}cBTC Balance: {eth_formatted:.6f} cBTC{Colors.RESET}")
            
            tokens = {
                "USDC": self.config["usdc_address"],
                "WCBTC": self.config["wcbtc_address"],
                "SUMA": self.config["suma_address"]
            }
            
            for symbol, address in tokens.items():
                balance_info = await self.get_token_balance(address, account.address)
                if balance_info:
                    print(f"{Colors.GREEN}{symbol} Balance: {balance_info['formatted']:.6f} {balance_info['symbol']}{Colors.RESET}")
                else:
                    print(f"{Colors.RED}{symbol} Balance: Error fetching balance{Colors.RESET}")
            
            print(f"{Colors.CYAN}{'='*35}{Colors.RESET}")
            
        except Exception as e:
            log.error(f"Error showing balances: {str(e)}")

    def show_transaction_history(self):
        if not self.transaction_history:
            log.info("No transaction history available")
            return
        
        print(f"\n{Colors.CYAN}=== Transaction History ==={Colors.RESET}")
        
        for i, tx in enumerate(self.transaction_history[-10:], 1):
            status_color = Colors.GREEN if tx["status"] == "success" else Colors.RED
            print(f"{Colors.WHITE}{i}. {tx['type'].upper()}{Colors.RESET}")
            print(f"   Status: {status_color}{tx['status']}{Colors.RESET}")
            print(f"   Hash: {Colors.CYAN}{tx['tx_hash']}{Colors.RESET}")
            print(f"   Time: {Colors.YELLOW}{tx['timestamp']}{Colors.RESET}")
            print()
        
        print(f"{Colors.CYAN}{'='*35}{Colors.RESET}")

    async def handle_menu_option(self, option):
        try:
            if option == "1":
                await self.start_automated_swaps()
            
            elif option == "2":
                try:
                    count = int(input("Enter transaction count: "))
                    if count > 0:
                        self.settings["transaction_count"] = count
                        self.save_user_settings()
                        log.success(f"Transaction count set to {count}")
                    else:
                        log.error("Transaction count must be positive")
                except ValueError:
                    log.error("Invalid transaction count")
            
            elif option == "3":
                print(f"\n{Colors.CYAN}=== Manual Swap ==={Colors.RESET}")
                token_in = input("Enter token in address: ").strip()
                token_out = input("Enter token out address: ").strip()
                
                try:
                    amount = float(input("Enter amount: "))
                    if amount > 0:
                        result = await self.perform_swap(self.private_keys[0], token_in, token_out, amount)
                        if result["success"]:
                            log.success("Manual swap completed successfully")
                        else:
                            log.error(f"Manual swap failed: {result.get('error', 'Unknown error')}")
                    else:
                        log.error("Amount must be positive")
                except ValueError:
                    log.error("Invalid amount")
            
            elif option == "4":
                print(f"\n{Colors.CYAN}=== Add Liquidity ==={Colors.RESET}")
                token_a = input("Enter token A address: ").strip()
                token_b = input("Enter token B address: ").strip()
                
                try:
                    amount_a = float(input("Enter amount A: "))
                    amount_b = float(input("Enter amount B: "))
                    
                    if amount_a > 0 and amount_b > 0:
                        result = await self.add_liquidity(self.private_keys[0], token_a, token_b, amount_a, amount_b)
                        if result["success"]:
                            log.success("Liquidity added successfully")
                        else:
                            log.error(f"Add liquidity failed: {result.get('error', 'Unknown error')}")
                    else:
                        log.error("Amounts must be positive")
                except ValueError:
                    log.error("Invalid amounts")
            
            elif option == "5":
                print(f"\n{Colors.CYAN}=== Convert SUMA to veSUMA ==={Colors.RESET}")
                
                try:
                    amount = float(input("Enter SUMA amount: "))
                    lock_days = int(input("Enter lock time (days): "))
                    
                    if amount > 0 and lock_days > 0:
                        result = await self.convert_to_vesuma(self.private_keys[0], amount, lock_days)
                        if result["success"]:
                            log.success("SUMA converted to veSUMA successfully")
                        else:
                            log.error(f"veSUMA conversion failed: {result.get('error', 'Unknown error')}")
                    else:
                        log.error("Amount and lock time must be positive")
                except ValueError:
                    log.error("Invalid input")
            
            elif option == "6":
                print(f"\n{Colors.CYAN}=== Convert veSUMA to SUMA ==={Colors.RESET}")
                result = await self.convert_vesuma_to_suma(self.private_keys[0])
                if result["success"]:
                    log.success("veSUMA converted to SUMA successfully")
                else:
                    log.error(f"veSUMA conversion failed: {result.get('error', 'Unknown error')}")

            elif option == "7":
                print(f"\n{Colors.CYAN}=== Stake veSUMA ==={Colors.RESET}")
                
                try:
                    amount = float(input("Enter veSUMA amount: "))
                    
                    if amount > 0:
                        result = await self.stake_vesuma(self.private_keys[0], amount)
                        if result["success"]:
                            log.success("veSUMA staked successfully")
                        else:
                            log.error(f"veSUMA staking failed: {result.get('error', 'Unknown error')}")
                    else:
                        log.error("Amount must be positive")
                except ValueError:
                    log.error("Invalid amount")
            
            elif option == "8":
                print(f"\n{Colors.CYAN}=== Vote with veSUMA ==={Colors.RESET}")
                
                gauge_address = input("Enter gauge address: ").strip()
                try:
                    weight = int(input("Enter vote weight: "))
                    
                    if weight > 0:
                        result = await self.vote_with_vesuma(self.private_keys[0], gauge_address, weight)
                        if result["success"]:
                            log.success("Voting completed successfully")
                        else:
                            log.error(f"Voting failed: {result.get('error', 'Unknown error')}")
                    else:
                        log.error("Weight must be positive")
                except ValueError:
                    log.error("Invalid weight")
            
            elif option == "9":
                await self.show_balances()
            
            elif option == "10":
                self.show_transaction_history()
            
            elif option == "11":
                log.info("Exiting Satsuma Bot...")
                return False
            
            else:
                log.error("Invalid option. Please choose 1-11.")
        
        except Exception as e:
            log.error(f"Unexpected error: {str(e)}")
        
        return True

    async def run(self):
        self.display_welcome_screen()
        log.success("Satsuma DeFi Bot initialized successfully!")
        
        while True:
            try:
                self.display_menu()
                choice = input(f"{Colors.WHITE}[➤] Select option (1-11): {Colors.RESET}").strip()
                
                if not choice:
                    continue
                
                should_continue = await self.handle_menu_option(choice)
                if not should_continue:
                    break
                
            except KeyboardInterrupt:
                log.info("\nBot stopped by user")
                break
            except Exception as e:
                log.error(f"Unexpected error: {str(e)}")
                continue

async def main():
    bot = SatsumaBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
