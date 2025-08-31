#!/usr/bin/env python3
"""
Supply PHRS into OpenFi (depositETH)
- Reads private keys from pvt.txt
- Asks user for min/max supply amount and number of txns
- Picks random amount between min and max for each txn
- Builds & sends depositETH tx
- Handles replay-attack errors gracefully
"""

from web3 import Web3, exceptions
import random
import time
from colorama import Fore, Style, init

# === Init Colorama ===
init(autoreset=True)

# === RPC Endpoint ===
RPC = "https://testnet.dplabs-internal.com"
w3 = Web3(Web3.HTTPProvider(RPC))

if not w3.is_connected():
    raise SystemExit(f"{Fore.RED}❌ Cannot connect to RPC {RPC}{Style.RESET_ALL}")

# === Contract Addresses ===
OPENFI_WPHRS = Web3.to_checksum_address("0x974828e18bff1e71780f9be19d0dff4fe1f61fca")
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

# === ABI for depositETH ===
deposit_abi = [{
    "inputs": [
        {"internalType": "address", "name": "lendingPool", "type": "address"},
        {"internalType": "address", "name": "onBehalfOf", "type": "address"},
        {"internalType": "uint16", "name": "referralCode", "type": "uint16"}
    ],
    "name": "depositETH",
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
}]
contract = w3.eth.contract(address=OPENFI_WPHRS, abi=deposit_abi)

# === Ask User for Parameters ===
min_amount = float(input("Enter minimum PHRS amount: ").strip())
max_amount = float(input("Enter maximum PHRS amount: ").strip())
num_txns   = int(input("Enter number of transactions per wallet: ").strip())

if min_amount <= 0 or max_amount <= 0 or min_amount > max_amount:
    raise SystemExit(f"{Fore.RED}❌ Invalid min/max values{Style.RESET_ALL}")

# === Load Private Keys ===
with open("pvt.txt") as f:
    private_keys = [line.strip() for line in f if line.strip()]

print(f"\n{Fore.YELLOW}🔑 Loaded {len(private_keys)} accounts{Style.RESET_ALL}\n")

# === Chain ID ===
try:
    chain_id = w3.eth.chain_id
except Exception:
    chain_id = None

for raw_pk in private_keys:
    pk = raw_pk if raw_pk.startswith("0x") else "0x" + raw_pk

    try:
        acct = w3.eth.account.from_key(pk)
    except Exception as e:
        print(f"{Fore.RED}❌ Invalid private key: {raw_pk[:8]}...  Error: {e}{Style.RESET_ALL}")
        continue

    addr = Web3.to_checksum_address(acct.address)
    balance = w3.eth.get_balance(addr)

    print(f"\n{Fore.CYAN}🔹 Wallet {addr} | Balance: {w3.from_wei(balance,'ether')} PHRS{Style.RESET_ALL}")

    for i in range(num_txns):
        # pick random amount
        amount = round(random.uniform(min_amount, max_amount), 6)  # 6 decimals safe
        amount_wei = w3.to_wei(amount, "ether")

        if balance < amount_wei:
            print(f"{Fore.YELLOW}⚠️  Skipping txn {i+1}: Insufficient balance{Style.RESET_ALL}")
            continue

        print(f"{Fore.GREEN}[{addr}] Txn {i+1}/{num_txns} | Supplying {amount} PHRS{Style.RESET_ALL}")

        try:
            # Build tx
            tx = contract.functions.depositETH(
                ZERO_ADDRESS,  # lendingPool param
                addr,          # onBehalfOf
                0              # referralCode
            ).build_transaction({
                "from": addr,
                "value": amount_wei,
                "gas": 400000,
                "maxFeePerGas": w3.to_wei("2", "gwei"),
                "maxPriorityFeePerGas": w3.to_wei("1", "gwei"),
                "nonce": w3.eth.get_transaction_count(addr),
                **({"chainId": chain_id} if chain_id else {})
            })

            # Sign & send
            signed = w3.eth.account.sign_transaction(tx, private_key=pk)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

            print(f"    📤 Sent: {Fore.CYAN}{w3.to_hex(tx_hash)}{Style.RESET_ALL}")

            # Optional: wait for receipt
            try:
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                status = f"{Fore.GREEN}✅ Success" if receipt.status == 1 else f"{Fore.RED}❌ Failed"
                print(f"    Block: {receipt.blockNumber}, Status: {status}{Style.RESET_ALL}")
            except Exception as e:
                print(f"    {Fore.YELLOW}⚠️ Pending/not confirmed: {e}{Style.RESET_ALL}")

            balance -= amount_wei
            time.sleep(1)  # small delay to avoid nonce race

        except exceptions.Web3RPCError as e:
            if hasattr(e, "args") and "TX_REPLAY_ATTACK" in str(e.args):
                print(f"{Fore.RED}⚠️ TX Replay Attack detected. Waiting 30s before retry...{Style.RESET_ALL}")
                time.sleep(30)
                continue
            else:
                print(f"{Fore.RED}❌ RPC Error: {e}{Style.RESET_ALL}")
                continue

        except Exception as e:
            print(f"{Fore.RED}❌ Unexpected Error: {e}{Style.RESET_ALL}")
            continue
