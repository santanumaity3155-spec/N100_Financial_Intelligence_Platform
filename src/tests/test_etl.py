"""Tests for the ETL extraction flow."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.etl.extract import DataExtractor


class ExtractTest(unittest.TestCase):
    def test_sectors_excel_uses_header_zero(self):
        """Sectors files should be read with header=0 instead of retrying with header=1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "sectors.xlsx"
            file_path.write_bytes(b"placeholder")

            with patch("src.etl.extract.pd.read_excel") as mock_read_excel:
                mock_read_excel.return_value = pd.DataFrame({"id": [1], "broad_sector": ["Industrials"]})

                extractor = DataExtractor(raw_data_dir=Path(tmpdir))
                extractor.read_excel_file(file_path, header=0)

                self.assertEqual(mock_read_excel.call_args.kwargs["header"], 0)


if __name__ == "__main__":
    unittest.main()
