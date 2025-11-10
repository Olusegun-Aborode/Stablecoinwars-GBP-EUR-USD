"""
Data Validation Module
Implements multi-source validation for data quality assurance
"""

import logging
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
    
    # External validation disabled: DeFiLlama checks removed to run supply/transfers only
    
    # Validate transfer counts
    if metrics.get('transfers_count', 0) < 0:
        logger.error(f"Invalid transfer count for {metrics['coin']}")
        return False
    
    # Validate transfer volume
    if metrics.get('transfers_volume', 0) < 0:
        logger.error(f"Invalid transfer volume for {metrics['coin']}")
        return False
    
    return True


    # DeFiLlama validation removed


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
