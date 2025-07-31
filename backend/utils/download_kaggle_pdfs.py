import pandas as pd
import requests
import os
import ast
import re

def parse_categories(cat_str):
    try:
        return ast.literal_eval(cat_str)
    except Exception:
        return []

def is_relevant_category(cat_list, target_categories):
    cat_list_lower = [c.lower() for c in cat_list]
    target_categories_lower = {c.lower() for c in target_categories}
    return any(c in target_categories_lower for c in cat_list_lower)

def sanitize_filename(filename):
    # Remove or replace all invalid file path chars for Windows
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def download_pdfs_from_csv(csv_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(csv_path)

    target_categories = {
        'cs.ai', 'i.2', 'i.2.0', 'i.2.1', 'i.2.2', 'i.2.3', 'i.2.4', 'i.2.5', 'i.2.6',
        'i.2.7', 'i.2.8', 'i.2.9', 'i.2.10', 'i.2.11', 'i.2.12',
        'cs.lg', 'cs.cl', 'cs.ma', 'cs.ne', 'cs.ds', 'cs.dl', 'cs.ro', 'cs.cv',
        'cs.lo', 'cs.db', 'cs.se', 'cs.hc', 'cs.sd', 'cs.sc', 'cs.ms',
        'stat.ml', 'stat.th', 'stat.co',
        'math.st', 'math.oc', 'math.co', 'math.ds',
        'f.4.1', 'd.1.6', 'd.3.2', 'g.3', 'h.2.8', 'h.3.3', 'h.5.2', 'j.4',
        '68txx', '03bxx', '90cxx'
    }

    df['parsed_categories'] = df['categories'].apply(parse_categories)
    filtered_df = df[df['parsed_categories'].apply(is_relevant_category, target_categories=target_categories)]
    valid_df = filtered_df[filtered_df['pdf_url'].notna() & (filtered_df['pdf_url'] != '')]

    print(f"Total rows in CSV: {len(df)}")
    print(f"Rows after category filtering: {len(filtered_df)}")
    print(f"Rows with valid PDF URLs: {len(valid_df)}")

    session = requests.Session()

    for i, row in valid_df.iterrows():
        pdf_url = row['pdf_url']
        entry_id_raw = str(row['entry_id']) if 'entry_id' in row else str(i)
        entry_id = sanitize_filename(entry_id_raw)
        fname = os.path.join(output_dir, f"arxiv_{entry_id}.pdf")

        if os.path.exists(fname):
            print(f"[{i}] Already downloaded: {fname}")
            continue

        print(f"[{i}] Downloading {pdf_url} ...")
        try:
            r = session.get(pdf_url, timeout=60)
            r.raise_for_status()
            with open(fname, 'wb') as f:
                f.write(r.content)
        except Exception as e:
            print(f"[{i}] Failed to download {pdf_url}: {e}")

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    csv_path = os.path.join(base_dir, "datasets", "arxiv_ai.csv")
    pdf_dir = os.path.join(base_dir, "datasets", "arxiv_ai_pdfs")

    download_pdfs_from_csv(csv_path, pdf_dir)
