"""
EVM Chain Data Extraction Module
Handles Ethereum
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from web3 import Web3
from web3.exceptions import BlockNotFound, ContractLogicError
import requests

logger = logging.getLogger(__name__)

# ERC20 Standard ABI (minimal for our needs)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
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
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    }
]

# RPC Endpoints (use environment variables in production)
RPC_ENDPOINTS = {
    'ethereum': os.getenv('ALCHEMY_ETH_URL', 'https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY'),
}

# Currency mapping
CURRENCY_MAP = {
    'GBPT': 'GBP', 'GBPA': 'GBP', 'tGBP': 'GBP', 'BGBP': 'GBP', 'VGBP': 'GBP',
    'EURC': 'EUR', 'EURS': 'EUR', 'EURCV': 'EUR', 'EURI': 'EUR', 'EURt': 'EUR',
    'USDC': 'USD', 'USDT': 'USD'
}


def get_web3_connection(chain: str, max_retries: int = 3) -> Optional[Web3]:
    """Get Web3 connection with retry logic."""
    endpoint = RPC_ENDPOINTS.get(chain)
    if not endpoint:
        logger.error(f"No RPC endpoint configured for {chain}")
        return None
    
    for attempt in range(max_retries):
        try:
            w3 = Web3(Web3.HTTPProvider(endpoint, request_kwargs={'timeout': 60}))
            if w3.is_connected():
                logger.debug(f"Connected to {chain} (attempt {attempt + 1})")
                return w3
            else:
                logger.warning(f"Failed to connect to {chain} (attempt {attempt + 1})")
        except Exception as e:
            logger.warning(f"Connection error for {chain} (attempt {attempt + 1}): {str(e)}")
        
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return None


def extract_evm_metrics(chain: str, symbol: str, address: str) -> Optional[Dict[str, Any]]:
    """
    Extract comprehensive metrics for an ERC20 stablecoin.
    
    Args:
        chain: Chain name (ethereum, polygon, etc.)
        symbol: Token symbol (EURC, GBPT, etc.)
        address: Contract address
    
    Returns:
        Dictionary with metrics or None if extraction fails
    """
    w3 = get_web3_connection(chain)
    if not w3:
        return None
    
    try:
        # Initialize contract
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(address),
            abi=ERC20_ABI
        )
        
        # Get current block
        current_block = w3.eth.block_number
        
        # Extract total supply
        total_supply_raw = contract.functions.totalSupply().call()
        decimals = contract.functions.decimals().call()
        total_supply = total_supply_raw / (10 ** decimals)
        
        # Calculate block range for last hour (assuming ~12s blocks for Ethereum)
        blocks_per_hour = {
            'ethereum': 300,  # ~12s blocks
        }
        from_block = max(0, current_block - blocks_per_hour.get(chain, 300))
        
        # Get Transfer events for the last hour
        try:
            transfer_filter = contract.events.Transfer.create_filter(
                fromBlock=from_block,
                toBlock='latest'
            )
            transfers = transfer_filter.get_all_entries()
            
            transfer_count = len(transfers)
            transfer_volume = sum(t['args']['value'] / (10 ** decimals) for t in transfers)
            
        except Exception as e:
            logger.warning(f"Could not fetch transfer events for {symbol} on {chain}: {str(e)}")
            transfer_count = 0
            transfer_volume = 0
        
        # Get peg price from CoinGecko (simplified - in production, use Chainlink oracle)
        peg_deviation = 0  # Placeholder - implement proper price oracle
        
        # Prepare metrics
        metrics = {
            'timestamp': datetime.utcnow(),
            'coin': symbol,
            'currency': CURRENCY_MAP.get(symbol, 'UNKNOWN'),
            'chain': chain,
            'supply': total_supply,
            'transfers_count': transfer_count,
            'transfers_volume': transfer_volume,
            'peg_deviation': peg_deviation,
            'tvl': 0,  # Will be enriched later
            'usd_equivalent_volume': 0  # Will be calculated later
        }
        
        return metrics
        
    except ContractLogicError as e:
        logger.error(f"Contract logic error for {symbol} on {chain}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error extracting {symbol} on {chain}: {str(e)}", exc_info=True)
        return None
