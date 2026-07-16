"""
Downloads a small starter corpus for RAG practice: PDFs (arXiv), Markdown
(docs repo), and plain text (Project Gutenberg) into Data/<type>/.
"""
import os
import urllib.request
import zipfile
import io

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data")

PDF_DIR = os.path.join(BASE_DIR, "pdf")
TXT_DIR = os.path.join(BASE_DIR, "text")
MD_DIR = os.path.join(BASE_DIR, "markdown")

ARXIV_PDFS = {
    "attention_is_all_you_need.pdf": "https://arxiv.org/pdf/1706.03762.pdf",
    "bert.pdf": "https://arxiv.org/pdf/1810.04805.pdf",
    "gpt3_few_shot_learners.pdf": "https://arxiv.org/pdf/2005.14165.pdf",
    "rag_paper.pdf": "https://arxiv.org/pdf/2005.11401.pdf",
    "chain_of_thought.pdf": "https://arxiv.org/pdf/2201.11903.pdf",
}

GUTENBERG_TXT = {
    "frankenstein.txt": "https://www.gutenberg.org/cache/epub/84/pg84.txt",
    "pride_and_prejudice.txt": "https://www.gutenberg.org/cache/epub/1342/pg1342.txt",
    "sherlock_holmes.txt": "https://www.gutenberg.org/cache/epub/1661/pg1661.txt",
    "moby_dick.txt": "https://www.gutenberg.org/cache/epub/2701/pg2701.txt",
    "alice_in_wonderland.txt": "https://www.gutenberg.org/cache/epub/11/pg11.txt",
}

# Zip of a docs-only repo (small, all markdown) - sindresorhus/awesome
MARKDOWN_ZIP_URL = "https://github.com/sindresorhus/awesome/archive/refs/heads/main.zip"


def download_file(url: str, dest_path: str):
    if os.path.exists(dest_path):
        print(f"skip (exists): {dest_path}")
        return
    print(f"downloading: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = response.read()
    with open(dest_path, "wb") as f:
        f.write(data)


def download_pdfs():
    os.makedirs(PDF_DIR, exist_ok=True)
    for filename, url in ARXIV_PDFS.items():
        download_file(url, os.path.join(PDF_DIR, filename))


def download_texts():
    os.makedirs(TXT_DIR, exist_ok=True)
    for filename, url in GUTENBERG_TXT.items():
        download_file(url, os.path.join(TXT_DIR, filename))


def download_markdown():
    os.makedirs(MD_DIR, exist_ok=True)
    print(f"downloading markdown repo zip: {MARKDOWN_ZIP_URL}")
    req = urllib.request.Request(MARKDOWN_ZIP_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        data = response.read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for member in z.namelist():
            if member.endswith(".md"):
                z.extract(member, MD_DIR)
    print(f"markdown files extracted to {MD_DIR}")


if __name__ == "__main__":
    download_pdfs()
    download_texts()
    download_markdown()
    print("done")
