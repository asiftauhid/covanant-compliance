"""Create a sample loan agreement PDF for local demo testing.

Parties are deidentified. Financial covenants are written as natural-language
undertakings; thresholds still align with the seeded demo data.
"""

from pathlib import Path

import fitz

MARGIN = 72
PAGE_WIDTH = 595
PAGE_HEIGHT = 842
FONT_SIZE = 10
LINE_HEIGHT = 13
FONTNAME = "helv"

SAMPLE_TEXT = """\
FACILITY AGREEMENT
Confidential - Demo Specimen

Date: 1 July 2026
Agreement No.: FA-2026-0041

This Facility Agreement (the "Agreement") is entered into as of the date first written above between:

(1) the company identified in Schedule 1 as the borrower (the "Borrower"); and
(2) the financial institution identified in Schedule 1 as the lender (the "Lender").

The Borrower and the Lender are each a "Party" and together the "Parties".

1. THE FACILITY

1.1 Subject to the terms of this Agreement, the Lender makes available to the Borrower a revolving credit facility in a maximum aggregate principal amount equal to the Commitment set out in Schedule 1 (the "Commitment").

1.2 The Borrower may draw, repay and re-borrow during the Availability Period, provided that the aggregate outstanding principal does not exceed the Commitment and no Event of Default is continuing.

1.3 Interest accrues on each drawn amount at the rate set out in Schedule 1, payable monthly in arrears on the last Business Day of each month.

1.4 The Facility matures on the Termination Date set out in Schedule 1, at which time all outstanding amounts become immediately due and payable.

2. PURPOSE

2.1 The Borrower shall apply all amounts borrowed under the Facility towards working capital and general corporate purposes of the Borrower, and not towards any purpose prohibited by applicable law or this Agreement.

3. CONDITIONS PRECEDENT

3.1 The Lender is not obliged to make the first utilisation available unless it has received, in form and substance satisfactory to it:

(a) a copy of this Agreement duly executed by the Borrower;
(b) evidence of the Borrower's corporate authority to enter into this Agreement;
(c) the most recent monthly financial statements of the Borrower; and
(d) confirmation that no Default is continuing.

4. FINANCIAL COVENANTS

4.1 The Borrower undertakes to the Lender that, for so long as any amount is outstanding under this Agreement, it shall comply with each of the following financial covenants. Compliance shall be tested monthly on the last Business Day of each calendar month by reference to the Borrower's monthly management accounts for that period.

4.2 Without limiting Clause 4.1, the Borrower shall:

(a) ensure that its debt service coverage ratio is not less than 1.25 times;

(b) ensure that its current ratio is at all times at least 1.20 times;

(c) ensure that its total debt does not at any time exceed USD 750,000;

(d) maintain a cash balance of not less than USD 50,000 at the end of each month;

(e) ensure that its leverage ratio does not exceed 8.0 times; and

(f) ensure that monthly revenue is not less than USD 300,000.

4.3 If the Borrower anticipates that any of the covenants in Clause 4.2 may not be met on the next testing date, it shall notify the Lender promptly and in any event no later than five (5) Business Days before that date.

5. INFORMATION UNDERTAKINGS

5.1 The Borrower shall deliver to the Lender, within fifteen (15) Business Days after the end of each calendar month:

(a) a balance sheet and income statement for that month; and
(b) a compliance certificate signed by an authorised officer, confirming whether each covenant in Clause 4.2 has been met.

5.2 The Borrower shall promptly notify the Lender of any Default, and of any material adverse change in its business, assets or financial condition.

5.3 Upon reasonable notice, the Borrower shall permit the Lender (or its advisors) to inspect its books and records during normal business hours.

6. GENERAL UNDERTAKINGS

6.1 The Borrower shall:

(a) maintain its corporate existence and the licences required for its business;
(b) comply in all material respects with applicable laws and regulations;
(c) maintain insurance customary for its business; and
(d) not create any security over its assets in favour of a third party, other than Permitted Security, without the prior written consent of the Lender.

6.2 The Borrower shall not, without the prior written consent of the Lender:

(a) declare or pay any dividend while a Default is continuing;
(b) incur additional Financial Indebtedness except for Permitted Indebtedness; or
(c) dispose of all or substantially all of its assets.

7. REPRESENTATIONS

7.1 The Borrower represents and warrants to the Lender on the date of this Agreement and on each Utilisation Date that:

(a) it is duly incorporated and validly existing under the laws of its jurisdiction;
(b) it has the power to enter into and perform this Agreement;
(c) this Agreement constitutes its legal, valid and binding obligations;
(d) the financial statements most recently delivered fairly present its financial condition; and
(e) no Default is continuing or would result from the proposed utilisation.

8. EVENTS OF DEFAULT

8.1 Each of the following is an Event of Default:

(a) Non-payment: the Borrower fails to pay any amount due under this Agreement when due, and such failure continues for three (3) Business Days;
(b) Financial covenants: any requirement of Clause 4 is not satisfied on a testing date and remains unremedied (if capable of remedy) for ten (10) Business Days;
(c) Other obligations: the Borrower fails to comply with any other material term of this Agreement and, if capable of remedy, fails to remedy within fifteen (15) Business Days of notice from the Lender;
(d) Misrepresentation: any representation in Clause 7 is incorrect in any material respect when made or deemed repeated;
(e) Insolvency: the Borrower becomes insolvent, suspends payments, or any insolvency proceeding is commenced in respect of it; or
(f) Cross-default: any other Financial Indebtedness of the Borrower is accelerated or becomes capable of being accelerated as a result of default.

8.2 On and at any time after an Event of Default is continuing, the Lender may by notice to the Borrower: cancel the Commitment; declare all or part of the outstanding amounts immediately due and payable; and/or exercise any other rights available under this Agreement or at law.

9. MISCELLANEOUS

9.1 Notices under this Agreement shall be in writing and delivered to the addresses set out in Schedule 1 (or any replacement address notified in writing).

9.2 No amendment of this Agreement is effective unless in writing and signed by each Party.

9.3 The Borrower may not assign or transfer any rights or obligations under this Agreement without the prior written consent of the Lender. The Lender may assign or transfer its rights to another financial institution.

9.4 This Agreement constitutes the entire agreement between the Parties in relation to the Facility and supersedes all prior discussions relating to it.

9.5 If any provision is held invalid or unenforceable, the remaining provisions continue in full force and effect.

9.6 This Agreement may be executed in counterparts, each of which is an original and all of which together form one instrument.

10. GOVERNING LAW AND JURISDICTION

10.1 This Agreement is governed by the laws of the Emirate of Dubai and the applicable federal laws of the United Arab Emirates.

10.2 The courts of Dubai have exclusive jurisdiction to settle any dispute arising out of or in connection with this Agreement.

SCHEDULE 1 - COMMERCIAL TERMS

Borrower:                 [DEIDENTIFIED - BORROWER]
Borrower jurisdiction:    [DEIDENTIFIED]
Lender:                   [DEIDENTIFIED - LENDER]
Lender branch:            [DEIDENTIFIED]
Commitment:               USD 5,000,000
Availability Period:      From the date of this Agreement to the date falling 11 months before the Termination Date
Termination Date:         30 June 2029
Interest rate:            Base Rate + 2.75% per annum
Testing Date:             Last Business Day of each calendar month
Reporting currency:       USD
Notice address (Borrower): As notified to the Lender in writing
Notice address (Lender):  As notified to the Borrower in writing

SCHEDULE 2 - PERMITTED ITEMS

Permitted Indebtedness means:
(a) indebtedness under this Agreement; and
(b) trade credit incurred in the ordinary course of business.

Permitted Security means:
(a) liens arising by operation of law in the ordinary course of business; and
(b) any security created with the prior written consent of the Lender.

IN WITNESS WHEREOF the Parties have executed this Agreement as of the date first written above.

Signed for and on behalf of the Borrower          Signed for and on behalf of the Lender

_______________________________                   _______________________________
Authorised Signatory                              Authorised Signatory

Name: [REDACTED]                                  Name: [REDACTED]
Title: [REDACTED]                                 Title: [REDACTED]
Date: ________________                            Date: ________________
"""


def _wrap_line(text: str, max_width: float) -> list[str]:
    if not text:
        return [""]
    if fitz.get_text_length(text, fontname=FONTNAME, fontsize=FONT_SIZE) <= max_width:
        return [text]

    words = text.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        width = fitz.get_text_length(candidate, fontname=FONTNAME, fontsize=FONT_SIZE)
        if width <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        # Extremely long token: hard-split.
        while fitz.get_text_length(word, fontname=FONTNAME, fontsize=FONT_SIZE) > max_width:
            lo, hi = 1, len(word)
            fit = 1
            while lo <= hi:
                mid = (lo + hi) // 2
                if fitz.get_text_length(word[:mid], fontname=FONTNAME, fontsize=FONT_SIZE) <= max_width:
                    fit = mid
                    lo = mid + 1
                else:
                    hi = mid - 1
            lines.append(word[:fit])
            word = word[fit:]
        current = word
    if current:
        lines.append(current)
    return lines or [""]


def create_sample_pdf(output_path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    y = MARGIN
    max_width = PAGE_WIDTH - 2 * MARGIN
    bottom = PAGE_HEIGHT - MARGIN

    for paragraph in SAMPLE_TEXT.splitlines():
        for line in _wrap_line(paragraph, max_width):
            if y + LINE_HEIGHT > bottom:
                page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
                y = MARGIN
            page.insert_text(
                (MARGIN, y),
                line,
                fontsize=FONT_SIZE,
                fontname=FONTNAME,
            )
            y += LINE_HEIGHT
        # Slight extra gap after blank source lines already handled by empty wrap.

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    page_count = doc.page_count
    doc.close()
    print(f"Created {output_path} ({page_count} pages)")


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    sample = root / "samples" / "loan_agreement_sample.pdf"
    create_sample_pdf(sample)

    public_copy = root / "frontend" / "public" / "loan_agreement_sample.pdf"
    if public_copy.parent.exists():
        public_copy.write_bytes(sample.read_bytes())
        print(f"Copied to {public_copy}")
