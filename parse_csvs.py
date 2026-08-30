#!/usr/bin/env python3
"""Parse all buyer/broker CSV files into unified JSON."""
import csv
import json
import os

CSV_DIR = '/home/localhost/Downloads'
OUTPUT = '/home/localhost/nepse-dashboard/portfolio_data.json'

files = {
    'Birendra': {
        'NMB': os.path.join(CSV_DIR, 'Birendra-NMB.csv'),
        'Laxmi Capital': os.path.join(CSV_DIR, 'Birendra-Laxmi_Capital.csv'),
    },
    'Maiya': {'Laxmi Capital': os.path.join(CSV_DIR, 'Maiya-Laxmi_Capital.csv')},
    'Binam': {'Laxmi Capital': os.path.join(CSV_DIR, 'Binam-Laxmi_Capital.csv')},
    'Janak': {'Laxmi Capital': os.path.join(CSV_DIR, 'Janak-Laxmi_Capital.csv')},
    'Junu': {'Laxmi Capital': os.path.join(CSV_DIR, 'Junu-Laxmi_Capital.csv')},
    'Sita': {'Laxmi Capital': os.path.join(CSV_DIR, 'Sita-Laxmi_Capital.csv')},
}

all_entries = []
stock_index = {}  # symbol -> aggregated info

for buyer, brokers in files.items():
    for broker, filepath in brokers.items():
        if not os.path.exists(filepath):
            print(f"SKIP: {filepath} not found")
            continue
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    symbol = row['Scrip'].strip()
                    balance = float(row['Current Balance'].replace(',', ''))
                    closing_price = float(row['Last Closing Price'].replace(',', ''))
                    closing_value = float(row['Value as of Last Closing Price'].replace(',', ''))
                    ltp = float(row['Last Transaction Price (LTP)'].replace(',', ''))
                    ltp_value = float(row['Value as of LTP'].replace(',', ''))
                except (ValueError, KeyError) as e:
                    continue

                entry = {
                    'symbol': symbol,
                    'buyer': buyer,
                    'broker': broker,
                    'shares': balance,
                    'closing_price': closing_price,
                    'closing_value': closing_value,
                    'ltp': ltp,
                    'ltp_value': ltp_value,
                }
                all_entries.append(entry)

                # Aggregate by symbol
                if symbol not in stock_index:
                    stock_index[symbol] = {
                        'symbol': symbol,
                        'total_shares': 0,
                        'total_value_ltp': 0,
                        'buyers': {},
                        'ltp': ltp,
                        'closing_price': closing_price,
                    }
                stock_index[symbol]['total_shares'] += balance
                stock_index[symbol]['total_value_ltp'] += ltp_value
                if buyer not in stock_index[symbol]['buyers']:
                    stock_index[symbol]['buyers'][buyer] = 0
                stock_index[symbol]['buyers'][buyer] += balance

# Sort by total value
stocks_sorted = sorted(stock_index.values(), key=lambda x: x['total_value_ltp'], reverse=True)

# Buyer summary
buyer_summary = {}
for buyer in files.keys():
    buyer_entries = [e for e in all_entries if e['buyer'] == buyer]
    total_shares = sum(e['shares'] for e in buyer_entries)
    total_value = sum(e['ltp_value'] for e in buyer_entries)
    unique_stocks = len(set(e['symbol'] for e in buyer_entries))
    buyer_summary[buyer] = {
        'total_shares': total_shares,
        'total_value': total_value,
        'unique_stocks': unique_stocks,
        'avg_value_per_stock': total_value / unique_stocks if unique_stocks else 0,
    }

output = {
    'stocks': stocks_sorted,
    'entries': all_entries,
    'buyer_summary': buyer_summary,
    'meta': {
        'total_stocks': len(stocks_sorted),
        'total_entries': len(all_entries),
        'total_value': sum(s['total_value_ltp'] for s in stocks_sorted),
        'total_shares': sum(s['total_shares'] for s in stocks_sorted),
    }
}

with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Parsed {len(all_entries)} entries across {len(stocks_sorted)} stocks")
print(f"Total portfolio value: NPR {output['meta']['total_value']:,.0f}")
print(f"Buyers: {list(buyer_summary.keys())}")
for b, info in buyer_summary.items():
    print(f"  {b}: {info['unique_stocks']} stocks, NPR {info['total_value']:,.0f}")
