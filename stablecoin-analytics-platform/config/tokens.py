"""
Token and Chain Configuration
Centralized configuration for all monitored stablecoins
"""

# Stablecoin contract addresses by chain
STABLECOINS = {
    "ethereum": {
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "EURC": "0x1aBaEA1f7C830bD89Acc67eC4af516284b1bC33c",
        "EURS": "0xdB25f211AB05b1c97D595516F45794528a807ad8",
        "tGBP": "0x00000000441378008EA67F4284A57932B1c000a5",
        "GBPT": "0x86B4dBE5D203e634a12364C0e428fa242A3FbA98",
    },
    "solana": {
        "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        "EURC": "HzwqbKZw8HxMN6bF2yFZNrht3c2iXXzpKcFu7uBEDKtr",
        "VGBP": "5H4voZhzySsVvwVYDAKku8MZGuYBC7cXaBKDPW4YHWW1",
    },
}

# Chain metadata
CHAINS = {
    "ethereum": {
        "name": "Ethereum",
        "type": "EVM",
        "block_time": 12,  # seconds
        "rpc_env_var": "ALCHEMY_ETH_URL"
    },
    "polygon": {
        "name": "Polygon",
        "type": "EVM",
        "block_time": 2,
        "rpc_env_var": "ALCHEMY_POLYGON_URL"
    },
    "base": {
        "name": "Base",
        "type": "EVM",
        "block_time": 2,
        "rpc_env_var": "ALCHEMY_BASE_URL"
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
