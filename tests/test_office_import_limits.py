import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from exam_mastery import fidelity


class OfficeLimits(unittest.TestCase):
    def test_direct_parser_entrypoints_enforce_inventory_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("example", b"abcd")
            for parser, args in [(fidelity._parse_pptx, (None, [])), (fidelity._parse_docx, (None,)),
                                 (fidelity._parse_spreadsheet, (None,))]:
                with self.subTest(parser=parser.__name__), patch.object(fidelity, "MAX_OFFICE_EXPANDED_BYTES", 3):
                    with self.assertRaisesRegex(ValueError, "expansion exceeds"):
                        parser(path, *args)
