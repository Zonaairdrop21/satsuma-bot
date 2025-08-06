from web3 import Web3
from dotenv import load_dotenv
import asyncio
import random
import time
import sys
import os
import json
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Configuration files
CONFIG_FILE = "satsuma_config.json"

# Terminal Colors for better visibility
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

# Standard ERC20 ABI for token interactions (balance, approval)
ERC20_ABI = [
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}
]

# Minimal ABI for the SWAP_ROUTER, including `exactInputSingle` and `multicall`
SWAP_ROUTER_ABI = [
    {
        "inputs": [
            {"components": [{"internalType": "address", "name": "tokenIn", "type": "address"}, {"internalType": "address", "name": "tokenOut", "type": "address"}, {"internalType": "address", "name": "deployer", "type": "address"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}, {"internalType": "uint256", "name": "amountIn", "type": "uint256"}, {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"}, {"internalType": "uint160", "name": "limitSqrtPrice", "type": "uint160"}], "internalType": "struct ISwapRouter.ExactInputSingleParams", "name": "params", "type": "tuple"}
        ],
        "name": "exactInputSingle",
        "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes[]", "name": "data", "type": "bytes[]"}],
        "name": "multicall",
        "outputs": [{"internalType": "bytes[]", "name": "results", "type": "bytes[]"}],
        "stateMutability": "payable",
        "type": "function"
    }
]

# Minimal ABI for the veSUMA contract, including `locked` function for checking lock time
VESUMA_ABI = [
    {
        "name": "locked",
        "inputs": [{"name": "arg0", "type": "address"}],
        "outputs": [
            {"name": "amount", "type": "uint256"},
            {"name": "end", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Minimal ABI for the Liquidity Router
LIQUIDITY_ROUTER_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "tokenA", "type": "address"}, {"internalType": "address", "name": "tokenB", "type": "address"}, {"internalType": "address", "name": "recipient", "type": "address"}, {"internalType": "uint256", "name": "amountA", "type": "uint256"}, {"internalType": "uint256", "name": "amountB", "type": "uint256"}, {"internalType": "uint256", "name": "amountAMin", "type": "uint256"}, {"internalType": "uint256", "name": "amountBMin", "type": "uint256"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "name": "addLiquidity", "outputs": [], "stateMutability": "payable", "type": "function"
    }
]

# Minimal ABI for Staking and Voting contracts
STAKING_VOTING_ABI = [
    {"inputs": [{"internalType": "uint256", "name": "_value", "type": "uint256"}], "name": "stake", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "_gauge_addr", "type": "address"}, {"internalType": "uint256", "name": "_weight", "type": "uint256"}], "name": "vote", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
]


class SatsumaBot:
    def __init__(self):
        self.config = self.load_config()
        self.w3 = self.initialize_provider()
        self.private_keys = self.get_private_keys()
        self.settings = self.load_user_settings()
        self.transaction_history = []
        self.token_addresses = {
            "cBTC": "0x0000000000000000000000000000000000000000",
            "USDC": Web3.to_checksum_address("0x2C8abD2A528D19AFc33d2eBA507c0F405c131335"),
            "WCBTC": Web3.to_checksum_address("0x8d0c9d1c17ae5e40fff9be350f57840e9e66cd93"),
            "SUMA": Web3.to_checksum_address("0xdE4251dd68e1aD5865b14Dd527E54018767Af58a"),
            "veSUMA": Web3.to_checksum_address("0x97a4f684620D578312Dc9fFBc4b0EbD8E804ab4a")
        }
        self.contracts = {
            "swap_router": self.w3.eth.contract(address=Web3.to_checksum_address("0x3012e9049d05b4b5369d690114d5a5861ebb85cb"), abi=SWAP_ROUTER_ABI),
            "liquidity_router": self.w3.eth.contract(address=Web3.to_checksum_address("0x55a4669cd6895EA25C174F13E1b49d69B4481704"), abi=LIQUIDITY_ROUTER_ABI),
            "vesuma": self.w3.eth.contract(address=self.token_addresses["veSUMA"], abi=VESUMA_ABI),
            "staking": self.w3.eth.contract(address=Web3.to_checksum_address("0x1234567890123456789012345678901234567892"), abi=STAKING_VOTING_ABI),
            "voting": self.w3.eth.contract(address=Web3.to_checksum_address("0x1234567890123456789012345678901234567891"), abi=STAKING_VOTING_ABI)
        }

    def load_config(self):
        config = {
            "rpc": "https://rpc.testnet.citrea.xyz",
            "chain_id": 5115,
            "explorer": "https://explorer.testnet.citrea.xyz",
        }
        return config

    def initialize_provider(self):
        try:
            w3 = Web3(Web3.HTTPProvider(self.config["rpc"]))
            if not w3.is_connected():
                raise Exception("Failed to connect to RPC")
            log.success(f"Connected to {self.config['rpc']}")
            return w3
        except Exception as e:
            log.error(f"Provider initialization failed: {str(e)}")
            sys.exit(1)

    def get_private_keys(self):
        key = os.getenv("PRIVATE_KEY_1")
        if not key:
            log.error("No private key found in environment variables.")
            sys.exit(1)
        return [key]

    def load_user_settings(self):
        user_settings = {"transaction_count": 0}
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    user_settings.update(json.load(f))
        except Exception as e:
            log.warn(f"Failed to load user settings: {e}")
        return user_settings

    def save_user_settings(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.settings, f, indent=2)

    def generate_random_amount(self):
        min_amount = 0.0001
        max_amount = 0.0002
        random_amount = random.uniform(min_amount, max_amount)
        return round(random_amount, 6)

    async def get_token_balance(self, token_address, account_address):
        if token_address == self.token_addresses["cBTC"]:
            balance = self.w3.eth.get_balance(account_address)
            return {"balance": balance, "decimals": 18, "symbol": "cBTC", "formatted": self.w3.from_wei(balance, 'ether')}
        try:
            token_contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
            balance = token_contract.functions.balanceOf(account_address).call()
            decimals = token_contract.functions.decimals().call()
            symbol = token_contract.functions.symbol().call()
            return {"balance": balance, "decimals": decimals, "symbol": symbol, "formatted": balance / (10 ** decimals)}
        except Exception as e:
            log.error(f"Error getting token balance: {e}")
            return None

    async def approve_token(self, account, token_address, spender_address, amount, nonce):
        if token_address == self.token_addresses["cBTC"]:
            return {"success": True, "nonce": nonce}
        try:
            token_contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
            allowance = token_contract.functions.allowance(account.address, spender_address).call()
            if allowance >= amount:
                log.success("Sufficient allowance exists.")
                return {"success": True, "nonce": nonce}
            approve_tx = token_contract.functions.approve(spender_address, amount).build_transaction({
                "from": account.address, "gas": 150000, "gasPrice": self.w3.eth.gas_price, "nonce": nonce
            })
            signed_tx = self.w3.eth.account.sign_transaction(approve_tx, private_key=account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            log.processing("Waiting for approval confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt["status"] == 1:
                log.success(f"Approval successful! Tx: {self.config['explorer']}/tx/{tx_hash.hex()}")
                return {"success": True, "nonce": nonce + 1}
            else:
                log.error("Approval transaction failed.")
                return {"success": False, "nonce": nonce}
        except Exception as e:
            log.error(f"Approval error: {e}")
            return {"success": False, "nonce": nonce}

    async def perform_swap(self, private_key, token_in, token_out, amount_in_float):
        try:
            account = self.w3.eth.account.from_key(private_key)
            log.step(f"Performing swap from {token_in} to {token_out} for {amount_in_float}")
            
            token_in_info = await self.get_token_balance(token_in, account.address)
            if not token_in_info: return {"success": False, "error": "Could not get token info"}
            
            amount_in_wei = int(amount_in_float * (10 ** token_in_info['decimals']))
            nonce = self.w3.eth.get_transaction_count(account.address)

            if token_in != self.token_addresses["cBTC"]:
                approval_result = await self.approve_token(account, token_in, self.contracts["swap_router"].address, amount_in_wei, nonce)
                if not approval_result["success"]: return {"success": False, "error": "Approval failed"}
                nonce = approval_result["nonce"]
            
            deadline = int(time.time()) + 300
            swap_params = {
                "tokenIn": token_in,
                "tokenOut": token_out,
                "deployer": Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
                "recipient": account.address,
                "deadline": deadline,
                "amountIn": amount_in_wei,
                "amountOutMinimum": 0,
                "limitSqrtPrice": 0
            }

            value_wei = amount_in_wei if token_in == self.token_addresses["cBTC"] else 0
            swap_tx = self.contracts["swap_router"].functions.exactInputSingle(swap_params).build_transaction({
                "from": account.address, "gas": 500000, "gasPrice": self.w3.eth.gas_price, "nonce": nonce, "value": value_wei
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(swap_tx, private_key=private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            log.processing("Waiting for swap confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt["status"] == 1:
                log.success(f"Swap successful! Tx: {self.config['explorer']}/tx/{tx_hash.hex()}")
                return {"success": True, "tx_hash": tx_hash.hex()}
            else:
                log.error("Swap transaction failed. Check explorer for details.")
                return {"success": False, "error": "Transaction failed"}
        except Exception as e:
            log.error(f"Swap error: {e}")
            return {"success": False, "error": str(e)}

    async def add_liquidity(self, private_key, token_a, token_b, amount_a, amount_b):
        try:
            account = self.w3.eth.account.from_key(private_key)
            log.step(f"Adding liquidity for {account.address} with {amount_a} {token_a} and {amount_b} {token_b}")
            
            token_a_info = await self.get_token_balance(token_a, account.address)
            token_b_info = await self.get_token_balance(token_b, account.address)
            
            if not token_a_info or not token_b_info:
                return {"success": False, "error": "Could not get token info"}
            
            amount_a_wei = int(amount_a * (10**token_a_info['decimals']))
            amount_b_wei = int(amount_b * (10**token_b_info['decimals']))
            
            nonce = self.w3.eth.get_transaction_count(account.address)

            approval_a = await self.approve_token(account, token_a, self.contracts["liquidity_router"].address, amount_a_wei, nonce)
            if not approval_a["success"]: return {"success": False, "error": "Token A approval failed"}
            nonce = approval_a['nonce']

            approval_b = await self.approve_token(account, token_b, self.contracts["liquidity_router"].address, amount_b_wei, nonce)
            if not approval_b["success"]: return {"success": False, "error": "Token B approval failed"}
            nonce = approval_b['nonce']
            
            deadline = int(time.time()) + 300
            
            liquidity_tx = self.contracts["liquidity_router"].functions.addLiquidity(
                token_a, token_b, account.address, amount_a_wei, amount_b_wei,
                0, 0, deadline
            ).build_transaction({
                "from": account.address,
                "gas": 500000, "gasPrice": self.w3.eth.gas_price, "nonce": nonce
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(liquidity_tx, private_key=private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            log.processing("Waiting for liquidity confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt["status"] == 1:
                log.success(f"Liquidity added successfully! Tx: {self.config['explorer']}/tx/{tx_hash.hex()}")
                return {"success": True, "tx_hash": tx_hash.hex()}
            else:
                log.error("Liquidity transaction failed.")
                return {"success": False, "error": "Transaction failed"}
        except Exception as e:
            log.error(f"Liquidity error: {e}")
            return {"success": False, "error": str(e)}

    async def convert_to_vesuma(self, private_key, amount, lock_time_days):
        try:
            account = self.w3.eth.account.from_key(private_key)
            log.step(f"Converting {amount} SUMA to veSUMA with lock time of {lock_time_days} days.")
            
            amount_wei = int(amount * 10**18)
            unlock_time = int(time.time()) + (lock_time_days * 24 * 60 * 60)
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            approve_result = await self.approve_token(account, self.token_addresses["SUMA"], self.token_addresses["veSUMA"], amount_wei, nonce)
            if not approve_result["success"]:
                log.error("SUMA approval failed")
                return {"success": False, "error": "Approval transaction failed"}
            
            nonce = approve_result["nonce"]
            
            selector = "0x12e82674"  # `create_lock` selector
            encoded_params = self.w3.abi.encode(['uint256', 'uint256'], [amount_wei, unlock_time])
            tx_data = selector + self.w3.to_hex(encoded_params)[2:]
            
            create_lock_tx = {
                "from": account.address, "to": self.token_addresses["veSUMA"],
                "gas": 500000, "gasPrice": self.w3.eth.gas_price, "nonce": nonce, "data": tx_data
            }
            
            signed_tx = self.w3.eth.account.sign_transaction(create_lock_tx, private_key=private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            log.processing("Waiting for veSUMA conversion confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt["status"] == 1:
                log.success(f"veSUMA conversion successful! Tx: {self.config['explorer']}/tx/{tx_hash.hex()}")
                return {"success": True, "tx_hash": tx_hash.hex()}
            else:
                log.error("veSUMA conversion failed: Transaction reverted.")
                return {"success": False, "error": "Transaction failed"}
        except Exception as e:
            log.error(f"veSUMA conversion error: {e}")
            return {"success": False, "error": str(e)}

    async def convert_vesuma_to_suma(self, private_key):
        try:
            account = self.w3.eth.account.from_key(private_key)
            log.step(f"Attempting to convert veSUMA to SUMA for {account.address}")
            
            try:
                locked_info = self.contracts["vesuma"].functions.locked(account.address).call()
                end_time = locked_info[1]
                current_time = int(time.time())
                
                if current_time < end_time:
                    lock_end_dt = datetime.fromtimestamp(end_time)
                    log.error(f"Lock period has not expired. Lock ends at {lock_end_dt}. Cannot withdraw veSUMA.")
                    return {"success": False, "error": "Lock period has not expired"}
            except Exception as e:
                log.warn(f"Could not check lock status: {e}. Attempting transaction anyway.")
            
            selector = "0x7f8661a1"  # `exit` selector
            tx_data = selector
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            exit_tx = {
                "from": account.address, "to": self.token_addresses["veSUMA"],
                "gas": 500000, "gasPrice": self.w3.eth.gas_price, "nonce": nonce, "data": tx_data
            }
            
            signed_tx = self.w3.eth.account.sign_transaction(exit_tx, private_key=private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            log.processing("Waiting for veSUMA -> SUMA conversion confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt["status"] == 1:
                log.success(f"veSUMA -> SUMA conversion successful! Tx: {self.config['explorer']}/tx/{tx_hash.hex()}")
                return {"success": True, "tx_hash": tx_hash.hex()}
            else:
                log.error("veSUMA -> SUMA conversion failed.")
                return {"success": False, "error": "Transaction failed"}
        except Exception as e:
            log.error(f"veSUMA -> SUMA conversion error: {e}")
            return {"success": False, "error": str(e)}

    async def stake_vesuma(self, private_key, amount):
        try:
            account = self.w3.eth.account.from_key(private_key)
            log.step(f"Staking {amount} veSUMA for {account.address}")
            
            amount_wei = int(amount * 10**18)
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            approve_result = await self.approve_token(account, self.token_addresses["veSUMA"], self.contracts["staking"].address, amount_wei, nonce)
            if not approve_result["success"]:
                log.error("veSUMA approval failed")
                return {"success": False, "error": "Approval transaction failed"}
            nonce = approve_result["nonce"]

            stake_tx = self.contracts["staking"].functions.stake(amount_wei).build_transaction({
                "from": account.address,
                "gas": 500000, "gasPrice": self.w3.eth.gas_price, "nonce": nonce
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(stake_tx, private_key=private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            log.processing("Waiting for staking confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt["status"] == 1:
                log.success(f"veSUMA staking successful! Tx: {self.config['explorer']}/tx/{tx_hash.hex()}")
                return {"success": True, "tx_hash": tx_hash.hex()}
            else:
                log.error("Staking transaction failed")
                return {"success": False, "error": "Transaction failed"}
        except Exception as e:
            log.error(f"Staking error: {e}")
            return {"success": False, "error": str(e)}

    async def vote_with_vesuma(self, private_key, gauge_address, weight):
        try:
            account = self.w3.eth.account.from_key(private_key)
            log.step(f"Voting with veSUMA for {account.address}")
            
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            vote_tx = self.contracts["voting"].functions.vote(gauge_address, weight).build_transaction({
                "from": account.address,
                "gas": 200000, "gasPrice": self.w3.eth.gas_price, "nonce": nonce
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(vote_tx, private_key=private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            log.processing("Waiting for voting confirmation...")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt["status"] == 1:
                log.success(f"Voting successful! Tx: {self.config['explorer']}/tx/{tx_hash.hex()}")
                return {"success": True, "tx_hash": tx_hash.hex()}
            else:
                log.error("Voting transaction failed")
                return {"success": False, "error": "Transaction failed"}
        except Exception as e:
            log.error(f"Voting error: {e}")
            return {"success": False, "error": str(e)}

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
        print(f"{Colors.YELLOW}10. Exit{Colors.RESET}")
        print(f"{Colors.YELLOW}{'='*35}{Colors.RESET}")
        
    async def show_balances(self):
        try:
            account = self.w3.eth.account.from_key(self.private_keys[0])
            log.info(f"Showing balances for {account.address}")
            
            print(f"\n{Colors.CYAN}=== Account Balances ==={Colors.RESET}")
            print(f"{Colors.WHITE}Address: {account.address}{Colors.RESET}")
            
            for symbol, address in self.token_addresses.items():
                balance_info = await self.get_token_balance(address, account.address)
                if balance_info:
                    print(f"{Colors.GREEN}{symbol} Balance: {balance_info['formatted']:.6f} {balance_info['symbol']}{Colors.RESET}")
                else:
                    print(f"{Colors.RED}{symbol} Balance: Error fetching balance{Colors.RESET}")
            
            print(f"{Colors.CYAN}{'='*35}{Colors.RESET}")
            
        except Exception as e:
            log.error(f"Error showing balances: {str(e)}")

    async def start_automated_swaps(self):
        if self.settings["transaction_count"] == 0:
            log.error("No transactions configured. Please set transaction count first.")
            return
        
        log.info(f"Starting automated swaps with {self.settings['transaction_count']} transactions")
        
        token_list = [self.token_addresses["USDC"], self.token_addresses["WCBTC"], self.token_addresses["SUMA"]]
        
        for i in range(self.settings["transaction_count"]):
            try:
                token_in = random.choice(token_list)
                token_out = random.choice([t for t in token_list if t != token_in])
                amount = self.generate_random_amount()
                private_key = random.choice(self.private_keys)
                
                log.info(f"Transaction {i+1}/{self.settings['transaction_count']}")
                
                result = await self.perform_swap(private_key, token_in, token_out, amount)
                
                if result["success"]:
                    log.success(f"Swap {i+1} completed successfully")
                else:
                    log.error(f"Swap {i+1} failed: {result.get('error', 'Unknown error')}")
                
                delay = random.uniform(5, 15)
                log.info(f"Waiting {delay:.1f} seconds before next transaction...")
                await asyncio.sleep(delay)
                
            except Exception as e:
                log.error(f"Error in transaction {i+1}: {str(e)}")
                continue
        
        log.success("Automated swaps completed!")

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
                token_in_name = input("Enter token to swap from (e.g., SUMA, USDC): ").strip().upper()
                token_out_name = input("Enter token to swap to: ").strip().upper()
                try:
                    amount = float(input("Enter amount: "))
                    if amount > 0 and token_in_name in self.token_addresses and token_out_name in self.token_addresses:
                        token_in = self.token_addresses[token_in_name]
                        token_out = self.token_addresses[token_out_name]
                        await self.perform_swap(self.private_keys[0], token_in, token_out, amount)
                    else:
                        log.error("Invalid token name or amount.")
                except ValueError:
                    log.error("Invalid amount")
            
            elif option == "4":
                print(f"\n{Colors.CYAN}=== Add Liquidity ==={Colors.RESET}")
                token_a_name = input("Enter token A (e.g., USDC, WCBTC): ").strip().upper()
                token_b_name = input("Enter token B: ").strip().upper()
                try:
                    amount_a = float(input(f"Enter amount for {token_a_name}: "))
                    amount_b = float(input(f"Enter amount for {token_b_name}: "))
                    
                    if token_a_name in self.token_addresses and token_b_name in self.token_addresses and amount_a > 0 and amount_b > 0:
                        token_a = self.token_addresses[token_a_name]
                        token_b = self.token_addresses[token_b_name]
                        await self.add_liquidity(self.private_keys[0], token_a, token_b, amount_a, amount_b)
                    else:
                        log.error("Invalid token name or amount.")
                except ValueError:
                    log.error("Invalid amounts")
            
            elif option == "5":
                print(f"\n{Colors.CYAN}=== Convert SUMA to veSUMA ==={Colors.RESET}")
                try:
                    amount = float(input("Enter SUMA amount: "))
                    lock_days = int(input("Enter lock time (days): "))
                    if amount > 0 and lock_days > 0:
                        await self.convert_to_vesuma(self.private_keys[0], amount, lock_days)
                    else:
                        log.error("Amount and lock time must be positive")
                except ValueError:
                    log.error("Invalid input")
            
            elif option == "6":
                await self.convert_vesuma_to_suma(self.private_keys[0])
            
            elif option == "7":
                print(f"\n{Colors.CYAN}=== Stake veSUMA ==={Colors.RESET}")
                try:
                    amount = float(input("Enter veSUMA amount to stake: "))
                    if amount > 0:
                        await self.stake_vesuma(self.private_keys[0], amount)
                    else:
                        log.error("Amount must be positive")
                except ValueError:
                    log.error("Invalid amount")

            elif option == "8":
                print(f"\n{Colors.CYAN}=== Vote with veSUMA ==={Colors.RESET}")
                try:
                    gauge_address = input("Enter gauge address: ").strip()
                    weight = int(input("Enter vote weight (0-100): "))
                    if 0 <= weight <= 100:
                        await self.vote_with_vesuma(self.private_keys[0], Web3.to_checksum_address(gauge_address), weight)
                    else:
                        log.error("Weight must be between 0 and 100")
                except ValueError:
                    log.error("Invalid input")
            
            elif option == "9":
                await self.show_balances()
            
            elif option == "10":
                log.info("Exiting Satsuma Bot...")
                return False
            
            else:
                log.error("Invalid option. Please choose 1-10.")
        
        except Exception as e:
            log.error(f"Unexpected error: {str(e)}")
        
        return True

    async def run(self):
        log.success("Satsuma DeFi Bot initialized successfully!")
        
        while True:
            try:
                self.display_menu()
                choice = input(f"{Colors.WHITE}[➤] Select option (1-10): {Colors.RESET}").strip()
                
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
