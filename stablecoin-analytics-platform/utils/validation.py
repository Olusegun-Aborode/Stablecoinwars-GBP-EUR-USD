"""
Data Validation Module
Implements multi-source validation for data quality assurance
"""

import logging
import requests
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Validation thresholds
SUPPLY_VARIANCE_THRESHOLD = 0.02  # 2% acceptable variance
MIN_SUPPLY_VALUE = 0  # Minimum valid supply
MAX_SUPPLY_VALUE = 1e15  # Maximum reasonable supply


def validate_metrics(metrics: Dict[str, Any]) -> bool:
    """
    Validate extracted metrics against multiple criteria.
    
    Args:
        metrics: Dictionary containing extracted metrics
    
    Returns:
        True if metrics pass validation, False otherwise
    """
    # Basic type guard
    if not isinstance(metrics, dict):
        logger.warning("Validation error: metrics is not a dict")
        return False

    # Check required fields
    required_fields = ['coin', 'currency', 'chain', 'timestamp', 'supply']
    for field in required_fields:
        if field not in metrics:
            logger.error(f"Missing required field: {field}")
            return False
    
    # Validate supply range
    supply = metrics.get('supply', 0)
    if supply < MIN_SUPPLY_VALUE or supply > MAX_SUPPLY_VALUE:
        logger.error(f"Supply {supply} out of valid range for {metrics['coin']}")
        return False
    
    # Validate against external source (DeFiLlama)
    if not validate_supply_against_defillama(metrics):
        logger.warning(f"Supply validation failed against DeFiLlama for {metrics['coin']}")
        # Don't fail completely, just log warning
    
    # Validate transfer counts
    if metrics.get('transfers_count', 0) < 0:
        logger.error(f"Invalid transfer count for {metrics['coin']}")
        return False
    
    # Validate transfer volume
    if metrics.get('transfers_volume', 0) < 0:
        logger.error(f"Invalid transfer volume for {metrics['coin']}")
        return False
    
    return True


def validate_supply_against_defillama(metrics: Dict[str, Any]) -> bool:
    """
    Cross-validate supply against DeFiLlama API.
    
    Args:
        metrics: Metrics dictionary with coin, chain, and supply
    
    Returns:
        True if validation passes or cannot be performed, False if significant discrepancy
    """
    # Token mapping to DeFiLlama identifiers
    token_map = {
        'EURC': 'eurc',
        'EURS': 'stasis-eurs',
        'USDC': 'usd-coin',
        'USDT': 'tether',
        # Add more as needed
    }
    
    # Guard against incomplete or non-dict metrics
    if not isinstance(metrics, dict):
        return True
    coin = metrics.get('coin')
    chain = metrics.get('chain', '')
    if not coin:
        return True

    token_id = token_map.get(coin)
    if not token_id:
        # No mapping available, skip validation
        return True
    
    try:
        url = f"https://stablecoins.llama.fi/stablecoin/{token_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Find supply for the specific chain
        if 'chainBalances' in data and isinstance(data['chainBalances'], list):
            for chain_data in data['chainBalances']:
                if chain_data.get('chain', '').lower() == chain.lower():
                    # Get circulating supply
                    llama_supply_data = chain_data.get('circulating', {})
                    llama_supply = float(llama_supply_data.get('peggedUSD', 0))
                    
                    # Convert to token amount (assuming ~$1 peg)
                    # In production, use actual price
                    extracted_supply = metrics.get('supply', 0)
                    
                    # Calculate variance
                    if llama_supply > 0:
                        variance = abs(extracted_supply - llama_supply) / llama_supply
                        
                        if variance > SUPPLY_VARIANCE_THRESHOLD:
                            logger.warning(
                                f"Supply variance {variance:.2%} exceeds threshold for {metrics['coin']} "
                                f"on {metrics['chain']} (extracted: {extracted_supply:.2f}, "
                                f"DeFiLlama: {llama_supply:.2f})"
                            )
                            return False
                        else:
                            logger.debug(
                                f"Supply validation passed for {metrics['coin']} "
                                f"(variance: {variance:.2%})"
                            )
                            return True
        
        # If we can't find the chain data, don't fail validation
        return True
        
    except requests.exceptions.RequestException as e:
        logger.debug(f"Could not validate against DeFiLlama: {str(e)}")
        return True  # Don't fail if external API is unavailable
    except Exception as e:
        logger.warning(f"Validation error: {str(e)}")
        return True


def validate_peg_stability(metrics: Dict[str, Any]) -> bool:
    """
    Validate that peg deviation is within acceptable range.
    
    Args:
        metrics: Metrics dictionary
    
    Returns:
        True if peg is stable, False if significant deviation
    """
    peg_deviation = abs(metrics.get('peg_deviation', 0))
    
    # Alert threshold: 0.5% deviation
    ALERT_THRESHOLD = 0.005
    
    if peg_deviation > ALERT_THRESHOLD:
        logger.warning(
            f"Significant peg deviation detected for {metrics['coin']}: "
            f"{peg_deviation:.4f} ({peg_deviation*100:.2f}%)"
        )
        return False
    
    return True
