"""Create a sample loan agreement PDF for local demo testing."""

from pathlib import Path

import fitz

SAMPLE_TEXT = """LOAN AND SECURITY AGREEMENT

Borrower: ABC Trading LLC
Lender: Gulf Capital Bank
Facility Amount: AED 5,000,000
Reporting Period: Monthly

SECTION 5 — FINANCIAL COVENANTS

5.1 Minimum Debt Service Coverage Ratio
Borrower shall maintain a Debt Service Coverage Ratio (DSCR) of not less than 1.25x,
tested monthly. DSCR is defined as Net Operating Income divided by Debt Service.

5.2 Minimum Current Ratio
Borrower shall maintain a Current Ratio of at least 1.20x, tested monthly.
Current Ratio is defined as Current Assets divided by Current Liabilities.

5.3 Maximum Total Debt
Total Debt shall not exceed AED 750,000 at any time during the term of this facility.
"""


def create_sample_pdf(output_path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    rect = fitz.Rect(72, 72, 523, 770)
    page.insert_textbox(rect, SAMPLE_TEXT, fontsize=11, fontname="helv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    doc.close()
    print(f"Created {output_path}")


if __name__ == "__main__":
    create_sample_pdf(Path(__file__).resolve().parent.parent / "samples" / "loan_agreement_sample.pdf")
