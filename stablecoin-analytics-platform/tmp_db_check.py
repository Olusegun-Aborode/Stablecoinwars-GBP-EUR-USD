import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('../.env', override=True)

from utils.db import get_db_connection

def main():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        print("=== Current Database State ===")
        cursor.execute(
            """
            SELECT 
                chain, 
                COUNT(*) as transfers, 
                TO_CHAR(MIN(timestamp), 'YYYY-MM-DD') as earliest, 
                TO_CHAR(MAX(timestamp), 'YYYY-MM-DD') as latest, 
                COUNT(DISTINCT DATE(timestamp)) as days_covered 
            FROM categorized_transfers 
            GROUP BY chain 
            ORDER BY chain 
            """
        )

        for row in cursor.fetchall():
            print(f"{row[0]:12s}: {row[1]:,} transfers | {row[2]} to {row[3]} | {row[4]} days")

        print("\n=== Currency Summary ===")
        cursor.execute(
            """
            SELECT 
                CASE 
                    WHEN token_symbol IN ('GBPT', 'tGBP', 'BGBP', 'VGBP') THEN 'GBP' 
                    WHEN token_symbol IN ('EURC', 'EURS', 'EURCV', 'EURI', 'EURt') THEN 'EUR' 
                    WHEN token_symbol IN ('USDC', 'USDT') THEN 'USD' 
                END as currency, 
                COUNT(*) as transfers, 
                COUNT(DISTINCT DATE(timestamp)) as days 
            FROM categorized_transfers 
            GROUP BY currency 
            ORDER BY transfers DESC 
            """
        )

        for row in cursor.fetchall():
            print(f"{row[0]:8s}: {row[1]:,} transfers | {row[2]} days")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\u2717 Database error: {e}")

if __name__ == '__main__':
    main()
