"""
API Integration Module
Handles external API calls for DeFi TVL and exchange rates
"""

import os
import logging
import requests
import time
import random
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# API Configuration
DEFILLAMA_BASE_URL = "https://stablecoins.llama.fi"


def fetch_defi_tvl(token_symbol: str, chain: str, max_retries: int = 3) -> float:
    """
    Fetch TVL for a specific stablecoin on a specific chain from DeFiLlama.
    Includes retry logic with exponential backoff.
    
    Args:
        token_symbol: Token symbol (EURC, GBPT, etc.)
        chain: Chain name
        max_retries: Maximum number of retry attempts
    
    Returns:
        TVL in USD or 0 if not found
    """
    # Map token symbols to DeFiLlama identifiers
    token_map = {
        'EURC': 'eurc',
        'EURS': 'stasis-eurs',
        'USDC': 'usd-coin',
        'USDT': 'tether',
        # Add more mappings as needed
    }
    
    token_id = token_map.get(token_symbol)
    if not token_id:
        logger.debug(f"No DeFiLlama mapping for {token_symbol}")
        return 0
    
    url = f"{DEFILLAMA_BASE_URL}/stablecoin/{token_id}"
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Fetching DeFiLlama data for {token_symbol} (attempt {attempt + 1}/{max_retries})")
            
            response = requests.get(url, timeout=10)
            
            # Log response status for diagnostics
            logger.debug(f"DeFiLlama response status: {response.status_code} for {token_symbol}")
            
            response.raise_for_status()
            
            # Robust JSON parsing with None guard
            data = response.json()
            if not data or not isinstance(data, dict):
                logger.warning(f"Invalid response from DeFiLlama for {token_symbol}: {data}")
                return 0
            
            # Find TVL for the specific chain
            if 'chainBalances' in data and isinstance(data['chainBalances'], list):
                for chain_data in data['chainBalances']:
                    if chain_data.get('chain', '').lower() == chain.lower():
                        # chainBalances contains circulating amount, not TVL
                        # For actual TVL in DeFi protocols, we'd need to query protocol-specific endpoints
                        circulating = float(chain_data.get('circulating', {}).get('peggedUSD', 0))
                        logger.debug(f"Found TVL for {token_symbol} on {chain}: ${circulating:,.2f}")
                        return circulating
            
            logger.debug(f"No TVL data found for {token_symbol} on {chain}")
            return 0
            
        except requests.exceptions.RequestException as e:
            # Status-aware backoff if available, otherwise generic
            status_code = getattr(e.response, 'status_code', None)
            logger.warning(f"API request failed for {token_symbol} TVL (attempt {attempt + 1}): {str(e)}; status={status_code}")
            
            if attempt < max_retries - 1:
                base_sleep = 2 ** attempt
                # Longer backoff on rate limits
                if status_code == 429:
                    base_sleep = max(base_sleep, 5)
                # Add small jitter to avoid thundering herd
                jitter = random.uniform(0.25, 0.75)
                sleep_time = base_sleep + jitter
                logger.debug(f"Retrying in {sleep_time:.2f}s...")
                time.sleep(sleep_time)
            else:
                logger.error(f"Max retries reached for {token_symbol} TVL")
                return 0
                
        except Exception as e:
            logger.error(f"Error fetching TVL for {token_symbol}: {str(e)}")
            return 0
    
    return 0


def get_exchange_rate(from_currency: str, to_currency: str = 'USD') -> float:
    """
    Get exchange rate from a currency to USD.
    Uses a free forex API.
    
    Args:
        from_currency: Source currency (GBP, EUR)
        to_currency: Target currency (default: USD)
    
    Returns:
        Exchange rate or 1.0 if fetch fails
    """
    try:
        # Using exchangerate-api.com (free tier)
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        rate = data.get('rates', {}).get(to_currency, 1.0)
        
        return float(rate)
        
    except Exception as e:
        logger.warning(f"Could not fetch exchange rate for {from_currency}/{to_currency}: {str(e)}")
        # Fallback to approximate rates
        fallback_rates = {
            'GBP': 1.27,
            'EUR': 1.09,
            'USD': 1.0
        }
        return fallback_rates.get(from_currency, 1.0)
