"""
Pipe Catalog Extractor

This module extracts pipe catalog data from the Technikkatalog Excel file
and converts it to CSV format for use in the NPV-based diameter optimizer.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PipeSpecification:
    """Data class for pipe specifications."""

    diameter_mm: float
    inner_diameter_mm: float
    outer_diameter_mm: float
    wall_thickness_mm: float
    material: str
    insulation_type: str
    thermal_conductivity_w_mk: float
    max_pressure_bar: float
    max_temperature_c: float
    cost_per_meter_eur: float


class PipeCatalogExtractor:
    """
    Extracts pipe catalog data from Technikkatalog Excel file.

    This class handles the extraction and processing of pipe specifications
    from the German Technikkatalog for district heating planning.
    """

    def __init__(self, excel_file_path: str):
        """
        Initialize the extractor with the Excel file path.

        Args:
            excel_file_path: Path to the Technikkatalog Excel file
        """
        self.excel_file_path = Path(excel_file_path)
        self.pipe_data: Optional[pd.DataFrame] = None

    def extract_pipe_catalog(self) -> pd.DataFrame:
        """
        Extract pipe catalog data from the Excel file.

        Returns:
            DataFrame containing pipe specifications

        Raises:
            FileNotFoundError: If Excel file doesn't exist
            ValueError: If required sheets are missing
        """
        if not self.excel_file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {self.excel_file_path}")

        logger.info(f"Extracting pipe catalog from: {self.excel_file_path}")

        try:
            # Read the Excel file - try different sheet names
            sheet_names = self._get_sheet_names()

            for sheet_name in sheet_names:
                try:
                    df = pd.read_excel(self.excel_file_path, sheet_name=sheet_name)
                    if self._is_pipe_catalog_sheet(df):
                        logger.info(f"Found pipe catalog in sheet: {sheet_name}")
                        self.pipe_data = self._process_pipe_data(df)
                        return self.pipe_data
                except Exception as e:
                    logger.debug(f"Could not read sheet {sheet_name}: {e}")
                    continue

            raise ValueError("No valid pipe catalog sheet found in Excel file")

        except Exception as e:
            logger.error(f"Error extracting pipe catalog: {e}")
            raise

    def _get_sheet_names(self) -> List[str]:
        """Get list of sheet names from Excel file."""
        try:
            excel_file = pd.ExcelFile(self.excel_file_path)
            return excel_file.sheet_names
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise

    def _is_pipe_catalog_sheet(self, df: pd.DataFrame) -> bool:
        """
        Check if DataFrame contains pipe catalog data.

        Args:
            df: DataFrame to check

        Returns:
            True if DataFrame contains pipe catalog data
        """
        # Look for typical pipe catalog columns
        pipe_columns = ["diameter", "durchmesser", "dn", "dn_", "rohr", "pipe"]
        df_columns = [col.lower() for col in df.columns]

        return any(pipe_col in " ".join(df_columns) for pipe_col in pipe_columns)

    def _process_pipe_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process and clean pipe catalog data.

        Args:
            df: Raw pipe catalog DataFrame

        Returns:
            Processed pipe catalog DataFrame
        """
        logger.info("Processing pipe catalog data")

        # Create a standardized DataFrame
        processed_data = []

        for _, row in df.iterrows():
            try:
                pipe_spec = self._extract_pipe_specification(row)
                if pipe_spec:
                    processed_data.append(
                        {
                            "diameter_mm": pipe_spec.diameter_mm,
                            "inner_diameter_mm": pipe_spec.inner_diameter_mm,
                            "outer_diameter_mm": pipe_spec.outer_diameter_mm,
                            "wall_thickness_mm": pipe_spec.wall_thickness_mm,
                            "material": pipe_spec.material,
                            "insulation_type": pipe_spec.insulation_type,
                            "thermal_conductivity_w_mk": pipe_spec.thermal_conductivity_w_mk,
                            "max_pressure_bar": pipe_spec.max_pressure_bar,
                            "max_temperature_c": pipe_spec.max_temperature_c,
                            "cost_per_meter_eur": pipe_spec.cost_per_meter_eur,
                        }
                    )
            except Exception as e:
                logger.debug(f"Error processing row: {e}")
                continue

        result_df = pd.DataFrame(processed_data)
        logger.info(f"Processed {len(result_df)} pipe specifications")
        return result_df

    def _extract_pipe_specification(self, row: pd.Series) -> Optional[PipeSpecification]:
        """
        Extract pipe specification from a DataFrame row.

        Args:
            row: DataFrame row containing pipe data

        Returns:
            PipeSpecification object or None if extraction fails
        """
        try:
            # Map column names to extract values
            diameter_mm = self._extract_numeric_value(row, ["diameter", "durchmesser", "dn", "dn_"])
            inner_diameter_mm = self._extract_numeric_value(
                row, ["inner_diameter", "innendurchmesser", "di"]
            )
            outer_diameter_mm = self._extract_numeric_value(
                row, ["outer_diameter", "aussendurchmesser", "da"]
            )
            wall_thickness_mm = self._extract_numeric_value(
                row, ["wall_thickness", "wandstärke", "s"]
            )

            # Extract material and insulation info
            material = self._extract_text_value(row, ["material", "werkstoff"])
            insulation_type = self._extract_text_value(row, ["insulation", "dämmung", "isolierung"])

            # Extract thermal and mechanical properties
            thermal_conductivity = self._extract_numeric_value(
                row, ["thermal_conductivity", "wärmeleitfähigkeit", "lambda"]
            )
            max_pressure = self._extract_numeric_value(row, ["max_pressure", "max_druck", "pn"])
            max_temperature = self._extract_numeric_value(
                row, ["max_temperature", "max_temperatur", "t_max"]
            )

            # Extract cost information
            cost_per_meter = self._extract_numeric_value(row, ["cost", "preis", "kosten", "eur_m"])

            # Validate required fields
            if diameter_mm is None:
                return None

            # Set defaults for missing values
            if inner_diameter_mm is None:
                inner_diameter_mm = diameter_mm - 2 * (wall_thickness_mm or 2.0)
            if outer_diameter_mm is None:
                outer_diameter_mm = diameter_mm + 2 * (wall_thickness_mm or 2.0)
            if wall_thickness_mm is None:
                wall_thickness_mm = (outer_diameter_mm - inner_diameter_mm) / 2
            if material is None:
                material = "Stahl"
            if insulation_type is None:
                insulation_type = "Standard"
            if thermal_conductivity is None:
                thermal_conductivity = 0.035  # Default for mineral wool
            if max_pressure is None:
                max_pressure = 16.0  # Default PN16
            if max_temperature is None:
                max_temperature = 120.0  # Default for DH
            if cost_per_meter is None:
                cost_per_meter = self._estimate_cost(diameter_mm)

            return PipeSpecification(
                diameter_mm=diameter_mm,
                inner_diameter_mm=inner_diameter_mm,
                outer_diameter_mm=outer_diameter_mm,
                wall_thickness_mm=wall_thickness_mm,
                material=material,
                insulation_type=insulation_type,
                thermal_conductivity_w_mk=thermal_conductivity,
                max_pressure_bar=max_pressure,
                max_temperature_c=max_temperature,
                cost_per_meter_eur=cost_per_meter,
            )

        except Exception as e:
            logger.debug(f"Error extracting pipe specification: {e}")
            return None

    def _extract_numeric_value(self, row: pd.Series, column_names: List[str]) -> Optional[float]:
        """Extract numeric value from row using multiple possible column names."""
        for col_name in column_names:
            for col in row.index:
                if col_name.lower() in str(col).lower():
                    try:
                        value = row[col]
                        if pd.notna(value):
                            return float(value)
                    except (ValueError, TypeError):
                        continue
        return None

    def _extract_text_value(self, row: pd.Series, column_names: List[str]) -> Optional[str]:
        """Extract text value from row using multiple possible column names."""
        for col_name in column_names:
            for col in row.index:
                if col_name.lower() in str(col).lower():
                    try:
                        value = row[col]
                        if pd.notna(value):
                            return str(value)
                    except (ValueError, TypeError):
                        continue
        return None

    def _estimate_cost(self, diameter_mm: float) -> float:
        """
        Estimate pipe cost based on diameter.

        Args:
            diameter_mm: Pipe diameter in mm

        Returns:
            Estimated cost per meter in EUR
        """
        # Simple cost estimation based on diameter
        base_cost = 50.0  # Base cost for small pipes
        diameter_factor = (diameter_mm / 50.0) ** 1.5  # Cost increases with diameter
        return base_cost * diameter_factor

    def save_to_csv(self, output_path: str) -> None:
        """
        Save extracted pipe catalog to CSV file.

        Args:
            output_path: Path for output CSV file
        """
        if self.pipe_data is None:
            raise ValueError("No pipe data extracted. Call extract_pipe_catalog() first.")

        output_file = Path(output_path)
        self.pipe_data.to_csv(output_file, index=False)
        logger.info(f"Pipe catalog saved to: {output_file}")

    def get_available_diameters(self) -> List[float]:
        """
        Get list of available pipe diameters.

        Returns:
            List of available diameters in mm
        """
        if self.pipe_data is None:
            raise ValueError("No pipe data extracted. Call extract_pipe_catalog() first.")

        return sorted(self.pipe_data["diameter_mm"].unique().tolist())


def main():
    """Main function to extract pipe catalog from Excel file."""
    try:
        # Initialize extractor
        excel_file = "Technikkatalog_Wärmeplanung_Version_1.1_August24_CC-BY.xlsx"
        extractor = PipeCatalogExtractor(excel_file)

        # Extract pipe catalog
        pipe_data = extractor.extract_pipe_catalog()

        # Save to CSV
        output_file = "data/csv/pipe_catalog.csv"
        extractor.save_to_csv(output_file)

        # Print summary
        print(f"Successfully extracted {len(pipe_data)} pipe specifications")
        print(f"Available diameters: {extractor.get_available_diameters()}")

    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()
