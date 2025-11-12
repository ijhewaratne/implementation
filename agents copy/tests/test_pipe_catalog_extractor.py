"""
Unit tests for pipe catalog extractor.
"""

import unittest
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
import sys

sys.path.append(str(Path(__file__).parent.parent / "src"))

from pipe_catalog_extractor import PipeCatalogExtractor, PipeSpecification


class TestPipeCatalogExtractor(unittest.TestCase):
    """Test cases for PipeCatalogExtractor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_excel_path = os.path.join(self.temp_dir, "test_catalog.xlsx")

        # Create test data
        self.test_data = pd.DataFrame(
            {
                "DN": [25, 32, 40, 50, 65],
                "Durchmesser_mm": [25, 32, 40, 50, 65],
                "Innendurchmesser_mm": [23, 30, 38, 48, 63],
                "Aussendurchmesser_mm": [27, 34, 42, 52, 67],
                "Wandstärke_mm": [2.0, 2.0, 2.0, 2.0, 2.0],
                "Material": ["Stahl", "Stahl", "Stahl", "Stahl", "Stahl"],
                "Dämmung": ["Standard", "Standard", "Standard", "Standard", "Standard"],
                "Wärmeleitfähigkeit_W_mK": [0.035, 0.035, 0.035, 0.035, 0.035],
                "Max_Druck_bar": [16.0, 16.0, 16.0, 16.0, 16.0],
                "Max_Temperatur_C": [120.0, 120.0, 120.0, 120.0, 120.0],
                "Kosten_EUR_m": [50, 60, 75, 100, 130],
            }
        )

        # Save test data to Excel
        with pd.ExcelWriter(self.test_excel_path, engine="openpyxl") as writer:
            self.test_data.to_excel(writer, sheet_name="Pipe_Catalog", index=False)

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_excel_path):
            os.remove(self.test_excel_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_init(self):
        """Test initialization."""
        extractor = PipeCatalogExtractor(self.test_excel_path)
        self.assertEqual(extractor.excel_file_path, Path(self.test_excel_path))
        self.assertIsNone(extractor.pipe_data)

    def test_get_sheet_names(self):
        """Test getting sheet names from Excel file."""
        extractor = PipeCatalogExtractor(self.test_excel_path)
        sheet_names = extractor._get_sheet_names()
        self.assertIn("Pipe_Catalog", sheet_names)

    def test_is_pipe_catalog_sheet(self):
        """Test pipe catalog sheet identification."""
        extractor = PipeCatalogExtractor(self.test_excel_path)

        # Test with pipe catalog data
        self.assertTrue(extractor._is_pipe_catalog_sheet(self.test_data))

        # Test with non-pipe data
        non_pipe_data = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        self.assertFalse(extractor._is_pipe_catalog_sheet(non_pipe_data))

    def test_extract_numeric_value(self):
        """Test numeric value extraction."""
        extractor = PipeCatalogExtractor(self.test_excel_path)

        # Create test row
        test_row = pd.Series({"DN": 25, "Durchmesser_mm": 25, "Kosten_EUR_m": 50.0})

        # Test successful extraction
        result = extractor._extract_numeric_value(test_row, ["durchmesser", "dn"])
        self.assertEqual(result, 25.0)

        # Test extraction with different column names
        result = extractor._extract_numeric_value(test_row, ["kosten", "eur"])
        self.assertEqual(result, 50.0)

        # Test extraction with non-existent column
        result = extractor._extract_numeric_value(test_row, ["nonexistent"])
        self.assertIsNone(result)

    def test_extract_text_value(self):
        """Test text value extraction."""
        extractor = PipeCatalogExtractor(self.test_excel_path)

        # Create test row
        test_row = pd.Series({"Material": "Stahl", "Dämmung": "Standard"})

        # Test successful extraction
        result = extractor._extract_text_value(test_row, ["material", "werkstoff"])
        self.assertEqual(result, "Stahl")

        # Test extraction with different column names
        result = extractor._extract_text_value(test_row, ["dämmung", "isolierung"])
        self.assertEqual(result, "Standard")

        # Test extraction with non-existent column
        result = extractor._extract_text_value(test_row, ["nonexistent"])
        self.assertIsNone(result)

    def test_extract_pipe_specification(self):
        """Test pipe specification extraction."""
        extractor = PipeCatalogExtractor(self.test_excel_path)

        # Create test row
        test_row = pd.Series(
            {
                "DN": 25,
                "Durchmesser_mm": 25,
                "Innendurchmesser_mm": 23,
                "Aussendurchmesser_mm": 27,
                "Wandstärke_mm": 2.0,
                "Material": "Stahl",
                "Dämmung": "Standard",
                "Wärmeleitfähigkeit_W_mK": 0.035,
                "Max_Druck_bar": 16.0,
                "Max_Temperatur_C": 120.0,
                "Kosten_EUR_m": 50.0,
            }
        )

        # Test successful extraction
        result = extractor._extract_pipe_specification(test_row)
        self.assertIsNotNone(result)
        self.assertEqual(result.diameter_mm, 25.0)
        self.assertEqual(result.inner_diameter_mm, 23.0)
        self.assertEqual(result.outer_diameter_mm, 27.0)
        self.assertEqual(result.wall_thickness_mm, 2.0)
        self.assertEqual(result.material, "Stahl")
        self.assertEqual(result.insulation_type, "Standard")
        self.assertEqual(result.thermal_conductivity_w_mk, 0.035)
        self.assertEqual(result.max_pressure_bar, 16.0)
        self.assertEqual(result.max_temperature_c, 120.0)
        self.assertEqual(result.cost_per_meter_eur, 50.0)

    def test_extract_pipe_specification_missing_diameter(self):
        """Test pipe specification extraction with missing diameter."""
        extractor = PipeCatalogExtractor(self.test_excel_path)

        # Create test row without diameter
        test_row = pd.Series({"Material": "Stahl", "Kosten_EUR_m": 50.0})

        # Test extraction should return None
        result = extractor._extract_pipe_specification(test_row)
        self.assertIsNone(result)

    def test_estimate_cost(self):
        """Test cost estimation."""
        extractor = PipeCatalogExtractor(self.test_excel_path)

        # Test cost estimation for different diameters
        cost_25 = extractor._estimate_cost(25.0)
        cost_50 = extractor._estimate_cost(50.0)
        cost_100 = extractor._estimate_cost(100.0)

        # Costs should increase with diameter
        self.assertLess(cost_25, cost_50)
        self.assertLess(cost_50, cost_100)

        # Costs should be positive
        self.assertGreater(cost_25, 0)
        self.assertGreater(cost_50, 0)
        self.assertGreater(cost_100, 0)

    def test_extract_pipe_catalog(self):
        """Test complete pipe catalog extraction."""
        extractor = PipeCatalogExtractor(self.test_excel_path)

        # Extract pipe catalog
        result = extractor.extract_pipe_catalog()

        # Check result
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 5)  # 5 test records
        self.assertIn("diameter_mm", result.columns)
        self.assertIn("cost_per_meter_eur", result.columns)

        # Check that pipe_data is set
        self.assertIsNotNone(extractor.pipe_data)
        self.assertEqual(len(extractor.pipe_data), 5)

    def test_get_available_diameters(self):
        """Test getting available diameters."""
        extractor = PipeCatalogExtractor(self.test_excel_path)
        extractor.extract_pipe_catalog()

        diameters = extractor.get_available_diameters()
        expected_diameters = [25.0, 32.0, 40.0, 50.0, 65.0]

        self.assertEqual(diameters, expected_diameters)

    def test_save_to_csv(self):
        """Test saving to CSV."""
        extractor = PipeCatalogExtractor(self.test_excel_path)
        extractor.extract_pipe_catalog()

        # Save to CSV
        csv_path = os.path.join(self.temp_dir, "test_output.csv")
        extractor.save_to_csv(csv_path)

        # Check that file exists
        self.assertTrue(os.path.exists(csv_path))

        # Check that file can be read
        df = pd.read_csv(csv_path)
        self.assertEqual(len(df), 5)
        self.assertIn("diameter_mm", df.columns)

    def test_save_to_csv_no_data(self):
        """Test saving to CSV without extracted data."""
        extractor = PipeCatalogExtractor(self.test_excel_path)

        # Try to save without extracting data
        csv_path = os.path.join(self.temp_dir, "test_output.csv")
        with self.assertRaises(ValueError):
            extractor.save_to_csv(csv_path)

    def test_get_available_diameters_no_data(self):
        """Test getting available diameters without extracted data."""
        extractor = PipeCatalogExtractor(self.test_excel_path)

        # Try to get diameters without extracting data
        with self.assertRaises(ValueError):
            extractor.get_available_diameters()

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        non_existent_path = "non_existent_file.xlsx"

        with self.assertRaises(FileNotFoundError):
            extractor = PipeCatalogExtractor(non_existent_path)
            extractor.extract_pipe_catalog()


if __name__ == "__main__":
    unittest.main()
