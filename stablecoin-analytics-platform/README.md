# Stablecoin Analytics Dashboard

**A production-ready data pipeline for tracking the supply, volume, and on-chain metrics of GBP, EUR, and USD stablecoins across major blockchains.**

This platform provides hourly extraction, validation, and storage of key stablecoin metrics, enabling real-time analysis of the evolving stablecoin landscape. It is designed for reliability, scalability, and easy extension.

---

## Features

- **Multi-Currency Tracking**: Monitors stablecoins pegged to GBP, EUR, and USD.
- **Multi-Chain Coverage**: Extracts data from 2 blockchains: Ethereum and Solana.
- **Automated Hourly Extraction**: A GitHub Actions workflow runs every hour to ensure data is always up-to-date.
- **Robust Data Pipeline**: Includes data validation, error handling with retries, and graceful fallbacks.
- **Centralized Database**: Stores all metrics in a PostgreSQL database (Neon) for easy querying and analysis.
- **Scalable Architecture**: Easily extendable to support new stablecoins and blockchains.
 - **Alert Logging**: Built-in logging for monitoring and failure visibility.

---

## Architecture

The data pipeline follows a classic ETL (Extract, Transform, Load) process, orchestrated by GitHub Actions.

```
+-------------------------+
|   GitHub Actions (Hourly) |
+-----------+-------------+
            | (triggers)
            v
+-------------------------+
|      main.py Script     |
+-----------+-------------+
            | (extracts from)
            v
+--------------------------------------------------------------------+
|                               Data Sources                         |
|                                                                    |
|  +-----------------+  +-----------------+  +----------------------+  |
|  |   EVM Chains    |  |     Solana      |  |   DeFiLlama API (TVL)  |  |
|  | (Alchemy RPC)   |  |  (Helius RPC)   |  |                        |  |
|  +-----------------+  +-----------------+  +----------------------+  |
|                                                                    |
+--------------------------------------------------------------------+
            | (validates & transforms)
            v
+-------------------------+
|  Data Validation &      |
|  Enrichment             |
+-----------+-------------+
            | (loads to)
            v
+-------------------------+
|   Neon PostgreSQL DB    |
+-----------+-------------+
            | (for analysis)
            v
+-------------------------+
|   Dune Analytics /      |
|   Metabase / etc.       |
+-------------------------+
```

---

## Data Coverage

The platform tracks the following stablecoins across Ethereum and Solana.

### GBP Stablecoins

| Token | Name | Chains |
|-------|------|--------|
| **GBPT** | Poundtoken | Ethereum |
| **tGBP** | Tokenised GBP | Ethereum |
| **BGBP** | Binance GBP | Ethereum |
| **VGBP** | VGBP | Solana |

### EUR Stablecoins

| Token | Name | Chains |
|-------|------|--------|
| **EURC** | Euro Coin | Ethereum |
| **EURS** | STASIS EURO | Ethereum |
| **EURCV**| EUR CoinVertible | Ethereum |
| **EURI** | Eurite | Ethereum |
| **EURt** | Tether EUR | Ethereum |

### USD Stablecoins (Benchmarks)

| Token | Name | Chains |
|-------|------|--------|
| **USDC** | USD Coin | Ethereum, Solana |
| **USDT** | Tether | Ethereum, Solana |

---

## Setup and Installation

### Prerequisites

1.  **Python 3.11**
2.  **Git**
3.  **GitHub Account**
4.  **Neon Account**: For the PostgreSQL database.
5.  **Alchemy Account**: For EVM chain RPC endpoints.
6.  **Helius Account** (Optional): For a dedicated Solana RPC endpoint.

### Local Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Olusegun-Aborode/Stablecoinwars-GBP-EUR-USD.git
    cd Stablecoinwars-GBP-EUR-USD
    ```

2.  **Create a virtual environment:**
    ```bash
    python3.11 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables:**
    - Create a `.env` file in the root directory.
    - Copy the contents of `.env.example` into it.
    - Fill in the required values for `NEON_DB_URL`, `ALCHEMY_ETH_URL`, etc.

---

## Configuration

All required credentials and endpoints are managed via environment variables.

### `.env` File

| Variable | Description | Required |
|---|---|---|
| `NEON_DB_URL` | Connection string for your Neon PostgreSQL database. | ✅ Yes |
| `ALCHEMY_ETH_URL` | Alchemy RPC endpoint for Ethereum. | ✅ Yes |
| `ALCHEMY_SOL_URL` | RPC endpoint for Solana. | ✅ Yes |

### GitHub Secrets

For the GitHub Actions workflow to run, you must add the same variables as **Repository secrets** under `Settings > Secrets and variables > Actions`.

---

## Usage

To run the extraction script manually:

```bash
python main.py
```

The script will log its progress to `extraction.log`.

---

## Automation

The project includes a GitHub Actions workflow (`.github/workflows/extract.yml`) that runs automatically:

- **On a schedule**: Every hour, on the hour (`cron: '0 * * * *'`).
- **Manually**: Can be triggered from the GitHub Actions tab.

---

## Database Schema

All metrics are stored in the `stablecoin_metrics` table.

| Column | Type | Description |
|---|---|---|
| `id` | SERIAL | Primary key. |
| `timestamp` | TIMESTAMPTZ | Timestamp of the extraction. |
| `coin` | VARCHAR(10) | Token symbol (e.g., GBPT, EURC). |
| `currency` | VARCHAR(5) | Pegged currency (GBP, EUR, USD). |
| `chain` | VARCHAR(20) | Blockchain name (e.g., ethereum, solana). |
| `supply` | NUMERIC | Total supply of the token on the chain. |
| `transfers_count` | INTEGER | Number of transfers in the last hour. |
| `transfers_volume` | NUMERIC | Total volume of transfers in the last hour. |
| `peg_deviation` | NUMERIC | (Future use) Deviation from the 1.0 peg. |
| `tvl` | NUMERIC | DeFiLlama-reported Total Value Locked. |
| `usd_equivalent_volume` | NUMERIC | Transfer volume converted to USD. |

---

## Project Structure

```
.
├── .github/workflows/extract.yml  # GitHub Actions workflow
├── config/
│   └── tokens.py                # Stablecoin contract addresses & metadata
├── extractor/
│   ├── api.py                   # DeFiLlama API extraction
│   ├── evm.py                   # EVM chain extraction logic
│   └── solana.py                # Solana chain extraction logic
├── utils/
│   ├── alerting.py              # Alert logging utility
│   ├── db.py                    # Database connection & insertion
│   └── validation.py            # Data validation logic
├── .env.example                 # Example environment file
├── main.py                      # Main extraction script
├── README.md                    # This file
└── requirements.txt             # Python dependencies
```

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
