# OpenFI – Automated Deposit Script

This repository contains a Python script to **supply PHRS into OpenFI** by calling the `depositETH` method on the lending pool contract.  
It supports **multiple wallets**, **randomized deposit amounts**, and **multiple transactions per wallet**.

---

## ✨ Features
- Reads private keys from `pvt.txt`
- Connects to OpenFI via Web3
- Executes `depositETH` calls
- User input for:
  - **Minimum amount (PHRS)**
  - **Maximum amount (PHRS)**
  - **Number of transactions per wallet**
- Randomizes deposit amount between min and max
- Signs & sends transactions automatically
- Prints transaction hash, block, and status
- Handles insufficient balance gracefully

---

## 📦 Requirements
- Python 3.8+
Install dependencies:
```bash
git clone https://github.com/deepakdhaka-1/Open-Fi-Lend-Borrow-Pharos-Testnet/
cd Open-Fi-Lend-Borrow-Pharos-Testnet
```
```
nano pvt.txt
```
```
python3 main.py
```

