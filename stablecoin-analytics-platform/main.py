#!/usr/bin/env python3
"""
Main extraction script for the Stablecoin Analytics Platform.
Orchestrates data extraction from multiple chains and sources.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Load environment variables from .env BEFORE importing modules that read os.getenv
from dotenv import load_dotenv
load_dotenv()

from extractor.evm import extract_evm_metrics
from extractor.solana import extract_solana_metrics
from utils.db import get_db_connection, insert_metrics
from utils.validation import validate_metrics
from config.tokens import STABLECOINS, CHAINS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extraction.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def extract_all_chains() -> List[Dict[str, Any]]:
    """Extract metrics from all configured chains."""
    all_metrics = []
    
    # Extract from EVM chains (ethereum only)
    for chain in ['ethereum']:
        if chain not in STABLECOINS:
            continue
            
        logger.info(f"Extracting data from {chain}...")
        try:
            for symbol, address in STABLECOINS[chain].items():
                # Skip invalid EVM addresses (e.g., placeholders like 'BGBP-CF3')
                if chain != 'solana' and not str(address).lower().startswith('0x'):
                    logger.warning(f"Skipping {symbol} on {chain}: invalid EVM address '{address}'")
                    continue
                metrics = extract_evm_metrics(chain, symbol, address)
                if metrics:
                    all_metrics.append(metrics)
                    logger.info(f"  ✓ {symbol} on {chain}: {metrics['supply']:.2f} supply")
        except Exception as e:
            logger.error(f"  ✗ Error extracting from {chain}: {str(e)}")

    # Extract from Solana
    if 'solana' in STABLECOINS:
        logger.info("Extracting data from Solana...")
        try:
            for symbol, address in STABLECOINS['solana'].items():
                metrics = extract_solana_metrics(symbol, address)
                if metrics:
                    all_metrics.append(metrics)
                    logger.info(f"  ✓ {symbol} on Solana: {metrics['supply']:.2f} supply")
        except Exception as e:
            logger.error(f"  ✗ Error extracting from Solana: {str(e)}")

    return all_metrics


def main():
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("Starting Stablecoin Analytics Platform extraction")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    logger.info("=" * 60)
    
    try:
        # Step 1: Extract metrics from all chains
        metrics = extract_all_chains()
        # Ensure only valid metric dictionaries are processed
        metrics = [m for m in metrics if isinstance(m, dict)]
        logger.info(f"Extracted {len(metrics)} metric records")
        
        if not metrics:
            logger.warning("No metrics extracted. Exiting.")
            return
        
        # Step 2: Validate metrics (TVL enrichment removed)
        logger.info("Validating extracted metrics...")
        validated_metrics = []
        for metric in metrics:
            if validate_metrics(metric):
                validated_metrics.append(metric)
            else:
                logger.warning(f"Validation failed for {metric['coin']} on {metric['chain']}")
        
        logger.info(f"{len(validated_metrics)}/{len(metrics)} metrics passed validation")
        
        # Step 3: Store in database
        if validated_metrics:
            logger.info("Storing metrics in database...")
            conn = get_db_connection()
            try:
                insert_metrics(conn, validated_metrics)
                conn.commit()
                logger.info(f"✓ Successfully stored {len(validated_metrics)} metrics")
            except Exception as e:
                conn.rollback()
                logger.error(f"Database insertion failed: {str(e)}")
                raise
            finally:
                conn.close()
        
        
        logger.info("=" * 60)
        logger.info("Extraction completed successfully")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.critical(f"Fatal error in main execution: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
