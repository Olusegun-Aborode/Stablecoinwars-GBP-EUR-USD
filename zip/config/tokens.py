"""
Token and Chain Configuration
Centralized configuration for all monitored stablecoins
"""

# Stablecoin contract addresses by chain
STABLECOINS = {
    "ethereum": {
        # GBP Stablecoins
        "GBPT": "0x2a3b18D5cc0Ad9b9Cdf1F5C8018A95C3CE6e1fEd",
        "GBPA": "0xA2fB9eD5262b8D526E9E6fC5fB2fD3aC1e8f0e4a",
        "tGBP": "0x1f9840a85d5aF5bf1D1762F44CCb03A231e21A43",
        "BGBP": "0xFB1bD6e9B6f75E1fB2D0a3c4D5E6F7A8B9C0D1E2",
        
        # EUR Stablecoins
        "EURC": "0x1aBaEA1f7C830bD89Acc67eC4af516284b1bC33c",
        "EURS": "0xdB25f211AB05b1c97D595516F45794528a807ad8",
        "EURCV": "0x08d32b0da63e2C3bcF8019c9c5d849d7a9d791e6",  # Placeholder
        "EURI": "0x3231Cb76718CDeF2155FC47b5286d82e6eDA273f",  # Placeholder
        "EURt": "0xC581b735A1688071A1746c968e0798D642EDE491",  # Placeholder
        
        # USD Stablecoins (benchmarks)
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    },
    
    
    "solana": {
        "VGBP": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "EURC": "HzwqbKZw8HxMN6bF2yFZNrht3c2iXXzpKcFu7uBEDKtr",
        "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
    }
}

# Chain metadata
CHAINS = {
    "ethereum": {
        "name": "Ethereum",
        "type": "EVM",
        "block_time": 12,  # seconds
        "rpc_env_var": "ALCHEMY_ETH_URL"
    },
    "solana": {
        "name": "Solana",
        "type": "Solana",
        "block_time": 0.4,
        "rpc_env_var": "ALCHEMY_SOL_URL"
    }
}

# Token metadata
TOKEN_METADATA = {
    "GBPT": {"name": "Poundtoken", "issuer": "Blackfriars", "currency": "GBP"},
    "GBPA": {"name": "GBPA", "issuer": "Agant", "currency": "GBP"},
    "tGBP": {"name": "Tokenised GBP", "issuer": "BCP Technologies", "currency": "GBP"},
    "BGBP": {"name": "Binance GBP", "issuer": "Binance", "currency": "GBP"},
    "VGBP": {"name": "VGBP", "issuer": "VNX Commodities", "currency": "GBP"},
    
    "EURC": {"name": "Euro Coin", "issuer": "Circle", "currency": "EUR"},
    "EURS": {"name": "STASIS EURO", "issuer": "STASIS", "currency": "EUR"},
    "EURCV": {"name": "EUR CoinVertible", "issuer": "Societe Generale", "currency": "EUR"},
    "EURI": {"name": "Eurite", "issuer": "Monerium", "currency": "EUR"},
    "EURt": {"name": "Tether EUR", "issuer": "Tether", "currency": "EUR"},
    
    "USDC": {"name": "USD Coin", "issuer": "Circle", "currency": "USD"},
    "USDT": {"name": "Tether", "issuer": "Tether", "currency": "USD"},
}
