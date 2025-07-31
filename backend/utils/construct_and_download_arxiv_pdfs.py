import pandas as pd
import os
import requests
from urllib.parse import quote

def arxiv_pdf_url(arxiv_id: str) -> str:
    """
    Construct the full PDF URL for an arXiv paper given its ID.
    Handles older and newer arxiv ID formats.
    """
    arxiv_id = arxiv_id.strip()
    # URL encode the id to be safe
    encoded_id = quote(arxiv_id)
    return f"https://arxiv.org/pdf/{encoded_id}.pdf"


def construct_pdf_urls(csv_path: str, arxiv_id_col: str = "arxiv_id") -> pd.DataFrame:
    """
    Loads CSV, constructs pdf URLs, and returns DataFrame with added 'pdf_url' column.
    """
    df = pd.read_csv(csv_path)
    if arxiv_id_col not in df.columns:
        raise ValueError(f"Column '{arxiv_id_col}' not found in CSV columns: {df.columns.tolist()}")
    
    df['pdf_url'] = df[arxiv_id_col].apply(arxiv_pdf_url)
    return df


def download_pdfs(df: pd.DataFrame, pdf_url_col: str, output_dir: str, id_col: str) -> None:
    """
    Download PDF files from URLs in the dataframe into the output directory.
    """
    os.makedirs(output_dir, exist_ok=True)
    session = requests.Session()

    for idx, row in df.iterrows():
        pdf_url = row[pdf_url_col]
        paper_id = row[id_col]
        filename = os.path.join(output_dir, f"{paper_id}.pdf")
        
        if os.path.exists(filename):
            print(f"[{idx}] Skipping already downloaded: {filename}")
            continue
        
        try:
            print(f"[{idx}] Downloading {pdf_url} ...")
            response = session.get(pdf_url, timeout=30)
            response.raise_for_status()
            with open(filename, 'wb') as f:
                f.write(response.content)
        except Exception as e:
            print(f"[{idx}] Failed to download {pdf_url}: {e}")


if __name__ == "__main__":
    # Set your paths here
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    csv_file_path = os.path.join(base_dir, "datasets", "arxiv_ai.csv")  # Adjust path to your csv
    pdf_output_dir = os.path.join(base_dir, "datasets", "arxiv_ai_pdfs")  # Where PDFs will be saved
    arxiv_id_column_name = "arxiv_id"  # Change this if your column name differs

    print(f"Constructing PDF URLs from arXiv IDs in: {csv_file_path}")

    # Construct URLs
    df_with_urls = construct_pdf_urls(csv_file_path, arxiv_id_col=arxiv_id_column_name)
    
    # Optional: save the CSV with PDF URLs
    output_csv_path = os.path.join(base_dir, "datasets", "arxiv_ai_with_pdf_urls.csv")
    df_with_urls.to_csv(output_csv_path, index=False)
    print(f"Saved CSV with PDF URLs at: {output_csv_path}")

    # Download PDFs
    print(f"Starting to download PDFs into: {pdf_output_dir}")
    download_pdfs(df_with_urls, pdf_url_col='pdf_url', output_dir=pdf_output_dir, id_col=arxiv_id_column_name)
    print("PDF download process completed.")
