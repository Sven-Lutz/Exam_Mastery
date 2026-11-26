"""Build synthetic four-product references and keep inspectable local evidence.

Usage: python scripts/verify_experience_references.py --out /absolute/local/path
No model/API calls. Outputs must stay outside the public Git repository.
"""
import argparse
import hashlib
import json
from pathlib import Path

from exam_mastery import anki_v2
from exam_mastery.learning.experience_pipeline import build


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    output = args.out.resolve()
    if output == repository or repository in output.parents:
        parser.error("Evidence must be outside the public repository")
    output.mkdir(parents=True, exist_ok=True)
    reports = {}
    for name in ("experience_binomial_reference", "experience_reference", "experience_finance_reference"):
        unit = json.loads((repository / "fixtures" / (name + ".json")).read_text())
        root = output / name
        first = build(unit, root)
        products = [root / path for path in first["products"].values()]
        mtimes = [path.stat().st_mtime_ns for path in products]
        second = build(unit, root)
        assert second["publication"]["status"] == "UNCHANGED"
        assert mtimes == [path.stat().st_mtime_ns for path in products]
        import pymupdf
        pdfs = {}
        release_hash = hashlib.sha256(b"".join(path.read_bytes() for path in products)).hexdigest()[:12]
        review = output / "review" / name / release_hash
        review.mkdir(parents=True, exist_ok=True)
        for filename in ("Lehrbuch.pdf", "Arbeitsbuch.pdf"):
            with pymupdf.open(root / filename) as pdf:
                pdfs[filename] = pdf.page_count
                for i, page in enumerate(pdf):
                    page.get_pixmap(matrix=pymupdf.Matrix(1, 1)).save(
                        review / (filename + f"-page-{i+1}.png"))
        preview = review / "anki"
        names = anki_v2.preview_html(root / "Anki.apkg", preview)
        from playwright.sync_api import sync_playwright
        browser_checks = []
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for width in (390, 1280):
                page = browser.new_page(viewport={"width": width, "height": 900})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto((root / "Interaktiv/index.html").as_uri())
                page.screenshot(path=str(review / f"interactive-{width}.png"), full_page=True)
                overflow = page.evaluate("document.documentElement.scrollWidth > innerWidth")
                assert not overflow and not errors, (overflow, errors)
                # Check generated fragment links against real semantic anchors.
                missing = page.locator('a[href^="#"]').evaluate_all(
                    "nodes => nodes.map(a=>a.getAttribute('href').slice(1)).filter(id=>!document.getElementById(id))")
                assert not missing, missing
                browser_checks.append({"width": width, "overflow": overflow, "page_errors": errors})
                page.close()
            browser.close()
        card_checks = anki_v2.screenshot(preview, names, preview, width=390)
        assert not any(check["horizontal_overflow"] for check in card_checks)
        reports[name] = {"first": first, "second": second, "pages": pdfs,
                         "browser": browser_checks, "anki_previews": len(names),
                         "entrypoint": str(root / "Interaktiv/index.html"),
                         "review_directory": str(review), "visual_review": "REQUIRED", "academic_acceptance": "NOT_APPROVED"}
    (output / "report.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(reports, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
