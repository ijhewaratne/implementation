#!/usr/bin/env python3
"""
Robust Pipe Catalog Builder

This script scans Technikkatalog Excel files, detects headers heuristically,
finds columns by keywords, normalizes EU/US numbers, and extracts pipe data
into a standardized schema.

Usage:
    python scripts/build_pipe_catalog.py \
        --xlsx /path/to/Technikkatalog.xlsx \
        --config configs/pipe_catalog_mapping.yaml \
        --out data/catalogs/pipe_catalog.csv
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import yaml
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class PipeCatalogBuilder:
    """
    Robust pipe catalog builder that extracts pipe specifications from Excel files.

    This class implements heuristic header detection, keyword-based column mapping,
    number normalization, and data validation to create standardized pipe catalogs.
    """

    def __init__(self, config_path: str):
        """
        Initialize the pipe catalog builder with configuration.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.column_mapping = self.config["columns"]
        self.sheet_names = self.config["sheet_names"]
        self.processing = self.config["processing"]
        self.output_schema = self.config["output_schema"]

        # Compile regex patterns for efficiency
        self._compile_patterns()

        logger.info(f"Initialized PipeCatalogBuilder with config: {config_path}")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        logger.info(f"Loaded configuration with {len(config.get('columns', {}))} column mappings")
        return config

    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficient matching."""
        self.compiled_patterns = {}

        for field, field_config in self.column_mapping.items():
            patterns = field_config.get("patterns", [])
            self.compiled_patterns[field] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

        logger.debug(
            f"Compiled {sum(len(patterns) for patterns in self.compiled_patterns.values())} regex patterns"
        )

    def detect_header_row(self, df: pd.DataFrame) -> int:
        """
        Detect the header row heuristically.

        Args:
            df: DataFrame to analyze

        Returns:
            Index of the header row
        """
        logger.info("Detecting header row heuristically...")

        # Strategy 1: Look for row with maximum keyword matches
        best_row = 0
        best_score = 0

        for row_idx in range(min(20, len(df))):  # Check first 20 rows
            row_text = " ".join(str(cell) for cell in df.iloc[row_idx] if pd.notna(cell))
            row_text_lower = row_text.lower()

            score = 0
            for field, field_config in self.column_mapping.items():
                keywords = field_config.get("keywords", [])
                for keyword in keywords:
                    if keyword.lower() in row_text_lower:
                        score += 1
                        break

            if score > best_score:
                best_score = score
                best_row = row_idx

        logger.info(f"Detected header row at index {best_row} with {best_score} keyword matches")
        return best_row

    def find_columns_by_keywords(self, df: pd.DataFrame, header_row: int) -> Dict[str, int]:
        """
        Find columns by matching keywords and patterns.

        Args:
            df: DataFrame to analyze
            header_row: Index of the header row

        Returns:
            Dictionary mapping field names to column indices
        """
        logger.info("Finding columns by keywords and patterns...")

        column_mapping = {}
        header_row_data = df.iloc[header_row]

        # Debug: Print header row content
        logger.debug(f"Header row {header_row} content: {header_row_data.tolist()}")

        for field, field_config in self.column_mapping.items():
            keywords = field_config.get("keywords", [])
            patterns = self.compiled_patterns.get(field, [])

            best_col = None
            best_score = 0

            for col_idx, col_value in enumerate(header_row_data):
                if pd.isna(col_value):
                    continue

                col_text = str(col_value).lower()
                logger.debug(f"Checking column {col_idx}: '{col_value}' for field '{field}'")

                # Check keywords
                for keyword in keywords:
                    if keyword.lower() in col_text:
                        score = len(keyword)  # Longer keywords get higher scores
                        logger.debug(
                            f"  Keyword match: '{keyword}' in '{col_text}' (score: {score})"
                        )
                        if score > best_score:
                            best_score = score
                            best_col = col_idx

                # Check patterns
                for pattern in patterns:
                    if pattern.search(col_text):
                        score = 10  # Pattern matches get high scores
                        logger.debug(
                            f"  Pattern match: '{pattern.pattern}' in '{col_text}' (score: {score})"
                        )
                        if score > best_score:
                            best_score = score
                            best_col = col_idx

            if best_col is not None:
                column_mapping[field] = best_col
                logger.info(
                    f"Mapped '{field}' to column {best_col} ('{header_row_data.iloc[best_col]}')"
                )
            else:
                logger.debug(f"No mapping found for field '{field}'")

        logger.info(f"Found {len(column_mapping)} column mappings")
        return column_mapping

    def normalize_number(self, value: Any, field: str) -> Optional[float]:
        """
        Normalize EU/US numbers to standard format.

        Args:
            value: Value to normalize
            field: Field name for context

        Returns:
            Normalized float value or None if invalid
        """
        if pd.isna(value) or value == "":
            return None

        value_str = str(value).strip()

        # Remove currency symbols and common prefixes
        currency_symbols = self.processing["number_formats"]["currency_symbols"]
        for symbol in currency_symbols:
            value_str = value_str.replace(symbol, "")

        # Handle German number format (comma as decimal separator)
        decimal_sep = self.processing["number_formats"]["decimal_separator"]
        thousands_sep = self.processing["number_formats"]["thousands_separator"]

        if decimal_sep == ",":
            # Replace German format with standard format
            value_str = value_str.replace(".", "")  # Remove thousands separator
            value_str = value_str.replace(",", ".")  # Replace decimal separator

        # Extract numeric value using regex
        number_match = re.search(r"[-+]?\d*[.,]?\d+", value_str)
        if not number_match:
            return None

        try:
            number = float(number_match.group())

            # Apply unit conversions if needed
            if field == "d_inner_m" or field == "d_outer_m":
                # Assume input is in mm, convert to m
                number *= self.processing["unit_conversions"]["mm_to_m"]
            elif field == "wall_thickness_mm":
                # Keep in mm
                pass
            elif field == "max_pressure_bar":
                # Keep in bar
                pass
            elif field == "max_temperature_c":
                # Keep in Celsius
                pass

            return number
        except (ValueError, TypeError):
            return None

    def extract_pipe_data(
        self, df: pd.DataFrame, column_mapping: Dict[str, int], sheet_name: str
    ) -> List[Dict[str, Any]]:
        """
        Extract pipe data from DataFrame using column mapping.

        Args:
            df: DataFrame containing pipe data
            column_mapping: Mapping of field names to column indices
            sheet_name: Name of the source sheet

        Returns:
            List of extracted pipe records
        """
        logger.info(f"Extracting pipe data from sheet '{sheet_name}'...")

        pipe_records = []
        defaults = self.processing["defaults"]
        validation = self.processing["validation"]

        # Start from row after header
        for row_idx in range(len(df)):
            if row_idx == 0:  # Skip header row
                continue

            row_data = df.iloc[row_idx]
            record = {"sheet": sheet_name}

            # Extract DN (nominal diameter) - required field
            if "dn" in column_mapping:
                dn_value = self.normalize_number(row_data.iloc[column_mapping["dn"]], "dn")
                if dn_value is None or dn_value < validation["min_diameter_mm"]:
                    continue  # Skip rows without valid DN
                record["dn"] = int(dn_value)
            else:
                continue  # Skip rows without DN column

            # Extract other fields
            for field, col_idx in column_mapping.items():
                if field == "dn":  # Already handled
                    continue

                value = row_data.iloc[col_idx]
                normalized_value = self.normalize_number(value, field)

                if normalized_value is not None:
                    # Apply validation
                    if field == "d_inner_m" and (
                        normalized_value < validation["min_diameter_mm"] * 0.001
                        or normalized_value > validation["max_diameter_mm"] * 0.001
                    ):
                        continue
                    elif field == "cost_eur_per_m" and (
                        normalized_value < validation["min_cost_eur_per_m"]
                        or normalized_value > validation["max_cost_eur_per_m"]
                    ):
                        continue
                    elif field == "u_wpermk" and (
                        normalized_value < validation["min_thermal_conductivity"]
                        or normalized_value > validation["max_thermal_conductivity"]
                    ):
                        continue

                    record[field] = normalized_value
                else:
                    # Use default value if available
                    if field in defaults:
                        record[field] = defaults[field]

            # Validate required fields
            required_fields = self.output_schema["required_fields"]
            if all(field in record for field in required_fields):
                pipe_records.append(record)

        logger.info(f"Extracted {len(pipe_records)} valid pipe records from sheet '{sheet_name}'")
        return pipe_records

    def find_pipe_catalog_sheets(self, excel_file: pd.ExcelFile) -> List[str]:
        """
        Find sheets that likely contain pipe catalog data.

        Args:
            excel_file: Excel file object

        Returns:
            List of sheet names containing pipe catalog data
        """
        logger.info("Finding pipe catalog sheets...")

        candidate_sheets = []

        for sheet_name in excel_file.sheet_names:
            # Check if sheet name matches any patterns
            sheet_lower = sheet_name.lower()

            for pattern in self.sheet_names:
                if "*" in pattern:
                    # Handle wildcard patterns
                    pattern_regex = pattern.replace("*", ".*")
                    if re.search(pattern_regex, sheet_lower, re.IGNORECASE):
                        candidate_sheets.append(sheet_name)
                        break
                elif pattern.lower() in sheet_lower:
                    candidate_sheets.append(sheet_name)
                    break

        logger.info(f"Found {len(candidate_sheets)} candidate sheets: {candidate_sheets}")
        return candidate_sheets

    def build_pipe_catalog(
        self, xlsx_path: str, output_path: str, preview_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build pipe catalog from Excel file.

        Args:
            xlsx_path: Path to Excel file
            output_path: Path for output CSV file
            preview_path: Path for preview JSON file (optional)

        Returns:
            Dictionary with build statistics
        """
        logger.info(f"Building pipe catalog from: {xlsx_path}")

        xlsx_path = Path(xlsx_path)
        if not xlsx_path.exists():
            raise FileNotFoundError(f"Excel file not found: {xlsx_path}")

        # Load Excel file
        excel_file = pd.ExcelFile(xlsx_path)
        logger.info(f"Loaded Excel file with {len(excel_file.sheet_names)} sheets")

        # Find pipe catalog sheets
        pipe_sheets = self.find_pipe_catalog_sheets(excel_file)
        if not pipe_sheets:
            logger.warning("No pipe catalog sheets found!")
            return {"status": "no_sheets_found", "records": 0}

        all_records = []
        sheet_stats = {}

        # Process each sheet
        for sheet_name in pipe_sheets:
            try:
                logger.info(f"Processing sheet: {sheet_name}")

                # Load sheet data
                df = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=None)

                # Detect header row
                header_row = self.detect_header_row(df)

                # Find columns by keywords
                column_mapping = self.find_columns_by_keywords(df, header_row)

                if not column_mapping:
                    logger.warning(f"No columns mapped in sheet: {sheet_name}")
                    continue

                # Extract pipe data
                records = self.extract_pipe_data(df, column_mapping, sheet_name)
                all_records.extend(records)
                sheet_stats[sheet_name] = len(records)

                logger.info(f"Extracted {len(records)} records from sheet: {sheet_name}")

            except Exception as e:
                logger.error(f"Error processing sheet {sheet_name}: {e}")
                continue

        if not all_records:
            logger.error("No pipe records extracted!")
            return {"status": "no_records_extracted", "records": 0}

        # Create DataFrame and save
        df_output = pd.DataFrame(all_records)

        # Ensure output directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save CSV
        df_output.to_csv(output_path, index=False)
        logger.info(f"Saved {len(all_records)} records to: {output_path}")

        # Save preview JSON
        if preview_path:
            preview_path = Path(preview_path)
            preview_path.parent.mkdir(parents=True, exist_ok=True)

            preview_data = {
                "summary": {
                    "total_records": len(all_records),
                    "sheets_processed": len(sheet_stats),
                    "output_path": str(output_path),
                },
                "sheet_statistics": sheet_stats,
                "sample_records": all_records[:5],  # First 5 records
                "column_mapping": self.column_mapping,
            }

            with open(preview_path, "w", encoding="utf-8") as f:
                json.dump(preview_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved preview to: {preview_path}")

        return {
            "status": "success",
            "records": len(all_records),
            "sheets_processed": len(sheet_stats),
            "sheet_statistics": sheet_stats,
            "output_path": str(output_path),
        }


def main():
    """Main function with CLI interface."""
    parser = argparse.ArgumentParser(
        description="Build pipe catalog from Technikkatalog Excel file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/build_pipe_catalog.py \\
    --xlsx Technikkatalog_Wärmeplanung_Version_1.1_August24_CC-BY.xlsx \\
    --config configs/pipe_catalog_mapping.yaml \\
    --out data/catalogs/pipe_catalog.csv

  python scripts/build_pipe_catalog.py \\
    --xlsx /path/to/Technikkatalog.xlsx \\
    --config configs/pipe_catalog_mapping.yaml \\
    --out data/catalogs/pipe_catalog.csv \\
    --preview data/catalogs/pipe_catalog_preview.json
        """,
    )

    parser.add_argument("--xlsx", required=True, help="Path to Technikkatalog Excel file")

    parser.add_argument("--config", required=True, help="Path to YAML configuration file")

    parser.add_argument("--out", required=True, help="Output path for CSV file")

    parser.add_argument("--preview", help="Output path for preview JSON file (optional)")

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Initialize builder
        builder = PipeCatalogBuilder(args.config)

        # Build pipe catalog
        result = builder.build_pipe_catalog(
            xlsx_path=args.xlsx, output_path=args.out, preview_path=args.preview
        )

        # Print results
        print("\n" + "=" * 60)
        print("PIPE CATALOG BUILD RESULTS")
        print("=" * 60)

        if result["status"] == "success":
            print(f"✅ Successfully built pipe catalog!")
            print(f"📊 Total records: {result['records']}")
            print(f"📋 Sheets processed: {result['sheets_processed']}")
            print(f"💾 Output file: {result['output_path']}")

            if args.preview:
                print(f"📄 Preview file: {args.preview}")

            print("\n📈 Sheet Statistics:")
            for sheet, count in result["sheet_statistics"].items():
                print(f"   • {sheet}: {count} records")

            print("\n🎉 Pipe catalog build completed successfully!")

        else:
            print(f"❌ Build failed: {result['status']}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error building pipe catalog: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
