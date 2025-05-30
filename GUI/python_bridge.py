"""
python_bridge.py

Bridges the Electron front-end to the synergy UMA logic.
Calls real PQC synergy code from synergy_uma.
"""

import sys
import os
import json

from synergy_uma.pq_keys import (
    generate_synergy_seed,
    save_synergy_info,
    load_synergy_info,
    derive_subkey_for_chain
)
from synergy_uma.sns_api import (
    register_name,
    lookup_name
)

# --------------------
# WALLET HANDLERS
# --------------------

def handle_wallet_list():
    wallet_dir = os.path.expanduser("~/.synergy/wallets")
    if not os.path.exists(wallet_dir):
        return {"success": True, "wallets": []}

    wallets = []
    for file in os.listdir(wallet_dir):
        if file.endswith(".json"):
            path = os.path.join(wallet_dir, file)
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    wallets.append({
                        "name": os.path.splitext(file)[0],
                        "address": data.get("synergy_address", "Unknown"),
                        "isDefault": False
                    })
            except:
                continue

    return {"success": True, "wallets": wallets}


def handle_wallet_create(name, password):
    try:
        wallet_dir = os.path.expanduser("~/.synergy/wallets")
        os.makedirs(wallet_dir, exist_ok=True)

        synergy_data = generate_synergy_seed(password)
        out_file = os.path.join(wallet_dir, f"{name}.json")
        save_synergy_info(out_file, synergy_data)

        print(f"[✅ Wallet Created] Saved to {out_file}", file=sys.stderr)  # Optional log for dev

        return {
            "success": True,
            "message": f"Wallet '{name}' created successfully.",
            "address": synergy_data["synergy_address"],
            "file": out_file
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_wallet_import(name, privateKey, password):
    return {"success": True, "message": f"Wallet '{name}' imported."}


def handle_wallet_show(address):
    return {
        "success": True,
        "wallet": {
            "name": "MyWallet",
            "address": address,
            "publicKey": "FAKEDATA123",
            "isDefault": True
        }
    }

# --------------------
# TOKEN HANDLERS
# --------------------

def handle_token_list():
    return {
        "success": True,
        "tokens": [
            {"id": "token1", "name": "MyToken", "symbol": "MTK", "supply": 1000, "type": "fungible"}
        ]
    }

def handle_token_create(name, symbol, tokenType, initialSupply, maxSupply, decimals):
    return {"success": True, "tokenId": "token123", "message": f"Created token {name}"}

def handle_token_mint(tokenId, amount, toAddress, password):
    return {"success": True, "message": f"Minted {amount} of {tokenId} to {toAddress}"}

# --------------------
# NAMING HANDLERS
# --------------------

def handle_naming_list():
    return {"success": True, "domains": [{"name": "alice.syn", "status": "registered", "expirationDate": 1699999999}]}

def handle_naming_check(domainName):
    if domainName == "alice.syn":
        return {"success": True, "available": False, "reason": "Name is taken"}
    return {"success": True, "available": True}

def handle_naming_register(domainName, registrationPeriod, password):
    synergy_file = "synergy_seed.json"
    try:
        synergy_data = load_synergy_info(synergy_file, password=password)
    except Exception as e:
        return {"success": False, "error": str(e)}

    if not synergy_data:
        return {"success": False, "error": f"No synergy data found or invalid password."}
    synergy_addr = synergy_data["synergy_address"]
    result = register_name(domainName, synergy_addr)
    return result

# --------------------
# UMA HANDLERS
# --------------------

def handle_uma_generate(password):
    synergy_data = generate_synergy_seed(password)
    out_file = "synergy_seed.json"
    save_synergy_info(out_file, synergy_data)
    return {
        "success": True,
        "synergy_address": synergy_data["synergy_address"],
        "file": out_file
    }

def handle_uma_derive(chainName, password):
    synergy_file = "synergy_seed.json"
    try:
        synergy_data = load_synergy_info(synergy_file, password=password)
    except Exception as e:
        return {"success": False, "error": str(e)}

    if not synergy_data:
        return {"success": False, "error": "No synergy seed loaded."}
    result = derive_subkey_for_chain(synergy_data, chainName, password)
    return result

# --------------------
# SNS LOOKUP
# --------------------

def handle_sns_lookup(domainName):
    res = lookup_name(domainName)
    return res

# --------------------
# MAIN ENTRY
# --------------------

def main():
    with open("bridge_out.log", "a") as f:
      f.write(f"[BRIDGE CALLED] Args: {sys.argv}\n")

    """
    python_bridge.py command [args...]
    """
    args = sys.argv
    if len(args) < 2:
        print(json.dumps({"success": False, "error": "No command"}))
        return

    command = args[1]

    try:
        if command == "wallet_list":
            resp = handle_wallet_list()

        elif command == "wallet_create":
            name = args[2]
            password = args[3]
            resp = handle_wallet_create(name, password)

        elif command == "wallet_import":
            name = args[2]
            privateKey = args[3]
            password = args[4]
            resp = handle_wallet_import(name, privateKey, password)

        elif command == "wallet_show":
            address = args[2]
            resp = handle_wallet_show(address)

        elif command == "token_list":
            resp = handle_token_list()

        elif command == "token_create":
            name = args[2]
            symbol = args[3]
            tokenType = args[4]
            initialSupply = args[5]
            maxSupply = args[6]
            decimals = args[7]
            resp = handle_token_create(name, symbol, tokenType, initialSupply, maxSupply, decimals)

        elif command == "token_mint":
            tokenId = args[2]
            amount = args[3]
            toAddress = args[4]
            password = args[5]
            resp = handle_token_mint(tokenId, amount, toAddress, password)

        elif command == "naming_list":
            resp = handle_naming_list()

        elif command == "naming_check":
            domainName = args[2]
            resp = handle_naming_check(domainName)

        elif command == "naming_register":
            domainName = args[2]
            registrationPeriod = args[3]
            password = args[4]
            resp = handle_naming_register(domainName, registrationPeriod, password)

        elif command == "uma_generate":
            password = ""
            if len(args) > 2:
                password = args[2]
            resp = handle_uma_generate(password)

        elif command == "uma_derive":
            chainName = args[2]
            password = ""
            if len(args) > 3:
                password = args[3]
            resp = handle_uma_derive(chainName, password)

        elif command == "sns_lookup":
            domainName = args[2]
            resp = handle_sns_lookup(domainName)

        else:
            resp = {"success": False, "error": f"Unknown command: {command}"}

        print(json.dumps(resp))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
