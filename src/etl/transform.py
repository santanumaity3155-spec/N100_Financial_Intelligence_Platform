"""
transform.py

Data transformation module for the N100 Financial Intelligence Platform.
Applies business rules and transformations to cleaned data.
"""

import logging
from typing import Dict, List, Optional, Any

import pandas as pd

from src.config.logging_config import get_logger

logger = get_logger(__name__)


class DataTransformer:
    """
    Transforms DataFrames according to business rules.
    
    Responsibilities:
    1. Apply dataset-specific transformations
    2. Calculate derived fields
    3. Standardize data formats
    4. Prepare data for loading
    """

    def __init__(self):
        """Initialize the DataTransformer."""
        self.transformation_log = []

    def transform_companies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform companies dataset.
        
        Parameters
        ----------
        df : pd.DataFrame
            Raw companies DataFrame
            
        Returns
        -------
        pd.DataFrame
            Transformed companies DataFrame
        """
        df = df.copy()
        logger.info("Transforming companies dataset")

        # Ensure company_id is string
        if "company_id" in df.columns:
            df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()

        # Clean company_name
        if "company_name" in df.columns:
            df["company_name"] = df["company_name"].astype(str).str.strip()

        # Clean sector
        if "sector" in df.columns:
            df["sector"] = df["sector"].astype(str).str.strip()

        # Clean industry
        if "industry" in df.columns:
            df["industry"] = df["industry"].astype(str).str.strip()

        # Normalize ISIN code
        if "isin_code" in df.columns:
            df["isin_code"] = df["isin_code"].astype(str).str.strip().str.upper()

        self.transformation_log.append({
            "dataset": "companies",
            "operations": ["clean_strings", "normalize_ids"]
        })

        return df

    def transform_profit_loss(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform profit and loss dataset.
        
        Parameters
        ----------
        df : pd.DataFrame
            Raw profit and loss DataFrame
            
        Returns
        -------
        pd.DataFrame
            Transformed profit and loss DataFrame
        """
        df = df.copy()
        logger.info("Transforming profit_loss dataset")

        # Normalize company_id
        if "company_id" in df.columns:
            df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()

        # Normalize period
        if "period" in df.columns:
            df["period"] = df["period"].astype(str).str.strip()

        # Convert numeric columns
        numeric_cols = [
            "revenue", "gross_profit", "operating_profit",
            "net_profit", "eps"
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        self.transformation_log.append({
            "dataset": "profit_loss",
            "operations": ["normalize_ids", "convert_numeric"]
        })

        return df

    def transform_balance_sheet(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform balance sheet dataset.
        
        Parameters
        ----------
        df : pd.DataFrame
            Raw balance sheet DataFrame
            
        Returns
        -------
        pd.DataFrame
            Transformed balance sheet DataFrame
        """
        df = df.copy()
        logger.info("Transforming balance_sheet dataset")

        # Normalize company_id
        if "company_id" in df.columns:
            df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()

        # Normalize period
        if "period" in df.columns:
            df["period"] = df["period"].astype(str).str.strip()

        # Convert numeric columns
        numeric_cols = [
            "total_assets", "total_liabilities", "total_equity",
            "current_assets", "current_liabilities", "cash_and_equivalents",
            "total_debt"
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        self.transformation_log.append({
            "dataset": "balance_sheet",
            "operations": ["normalize_ids", "convert_numeric"]
        })

        return df

    def transform_cash_flow(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform cash flow dataset.
        
        Parameters
        ----------
        df : pd.DataFrame
            Raw cash flow DataFrame
            
        Returns
        -------
        pd.DataFrame
            Transformed cash flow DataFrame
        """
        df = df.copy()
        logger.info("Transforming cash_flow dataset")

        # Normalize company_id
        if "company_id" in df.columns:
            df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()

        # Normalize period
        if "period" in df.columns:
            df["period"] = df["period"].astype(str).str.strip()

        # Convert numeric columns
        numeric_cols = [
            "operating_cash_flow", "investing_cash_flow",
            "financing_cash_flow", "free_cash_flow"
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        self.transformation_log.append({
            "dataset": "cash_flow",
            "operations": ["normalize_ids", "convert_numeric"]
        })

        return df

    def transform_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform analysis dataset.
        
        Parameters
        ----------
        df : pd.DataFrame
            Raw analysis DataFrame
            
        Returns
        -------
        pd.DataFrame
            Transformed analysis DataFrame
        """
        df = df.copy()
        logger.info("Transforming analysis dataset")

        # Normalize company_id
        if "company_id" in df.columns:
            df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()

        # Normalize period
        if "period" in df.columns:
            df["period"] = df["period"].astype(str).str.strip()

        # Clean analysis_type
        if "analysis_type" in df.columns:
            df["analysis_type"] = df["analysis_type"].astype(str).str.strip()

        self.transformation_log.append({
            "dataset": "analysis",
            "operations": ["normalize_ids", "clean_strings"]
        })

        return df

    def transform_documents(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform documents dataset.
        
        Parameters
        ----------
        df : pd.DataFrame
            Raw documents DataFrame
            
        Returns
        -------
        pd.DataFrame
            Transformed documents DataFrame
        """
        df = df.copy()
        logger.info("Transforming documents dataset")

        # Normalize company_id
        if "company_id" in df.columns:
            df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()

        # Clean document_type
        if "document_type" in df.columns:
            df["document_type"] = df["document_type"].astype(str).str.strip()

        # Clean document_url
        if "document_url" in df.columns:
            df["document_url"] = df["document_url"].astype(str).str.strip()

        self.transformation_log.append({
            "dataset": "documents",
            "operations": ["normalize_ids", "clean_strings"]
        })

        return df

    def transform_pros_cons(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform pros and cons dataset.
        
        Parameters
        ----------
        df : pd.DataFrame
            Raw pros and cons DataFrame
            
        Returns
        -------
        pd.DataFrame
            Transformed pros and cons DataFrame
        """
        df = df.copy()
        logger.info("Transforming pros_cons dataset")

        # Normalize company_id
        if "company_id" in df.columns:
            df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()

        # Clean pros and cons
        if "pros" in df.columns:
            df["pros"] = df["pros"].astype(str).str.strip()

        if "cons" in df.columns:
            df["cons"] = df["cons"].astype(str).str.strip()

        # Normalize analysis_period
        if "analysis_period" in df.columns:
            df["analysis_period"] = df["analysis_period"].astype(str).str.strip()

        self.transformation_log.append({
            "dataset": "pros_cons",
            "operations": ["normalize_ids", "clean_strings"]
        })

        return df

    def transform_sectors(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform sectors dataset.
        
        Parameters
        ----------
        df : pd.DataFrame
            Raw sectors DataFrame
            
        Returns
        -------
        pd.DataFrame
            Transformed sectors DataFrame
        """
        df = df.copy()
        logger.info("Transforming sectors dataset")

        # Normalize sector_id
        if "sector_id" in df.columns:
            df["sector_id"] = df["sector_id"].astype(str).str.strip().str.upper()

        # Clean sector_name
        if "sector_name" in df.columns:
            df["sector_name"] = df["sector_name"].astype(str).str.strip()

        # Clean sector_description
        if "sector_description" in df.columns:
            df["sector_description"] = df["sector_description"].astype(str).str.strip()

        self.transformation_log.append({
            "dataset": "sectors",
            "operations": ["normalize_ids", "clean_strings"]
        })

        return df

    def transform_stock_prices(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform stock prices dataset.
        
        Parameters
        ----------
        df : pd.DataFrame
            Raw stock prices DataFrame
            
        Returns
        -------
        pd.DataFrame
            Transformed stock prices DataFrame
        """
        df = df.copy()
        logger.info("Transforming stock_prices dataset")

        # Normalize company_id
        if "company_id" in df.columns:
            df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()

        # Normalize date
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors='coerce')
            df["date"] = df["date"].dt.strftime("%Y-%m-%d")

        # Convert numeric columns
        numeric_cols = [
            "open_price", "high_price", "low_price",
            "close_price", "volume"
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        self.transformation_log.append({
            "dataset": "stock_prices",
            "operations": ["normalize_ids", "normalize_dates", "convert_numeric"]
        })

        return df

    def transform_market_cap(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform market cap dataset.
        
        Parameters
        ----------
        df : pd.DataFrame
            Raw market cap DataFrame
            
        Returns
        -------
        pd.DataFrame
            Transformed market cap DataFrame
        """
        df = df.copy()
        logger.info("Transforming market_cap dataset")

        # Normalize company_id
        if "company_id" in df.columns:
            df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()

        # Normalize date
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors='coerce')
            df["date"] = df["date"].dt.strftime("%Y-%m-%d")

        # Convert numeric columns
        numeric_cols = [
            "market_cap", "enterprise_value", "shares_outstanding"
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        self.transformation_log.append({
            "dataset": "market_cap",
            "operations": ["normalize_ids", "normalize_dates", "convert_numeric"]
        })

        return df

    def transform_financial_ratios(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform financial ratios dataset.
        
        Parameters
        ----------
        df : pd.DataFrame
            Raw financial ratios DataFrame
            
        Returns
        -------
        pd.DataFrame
            Transformed financial ratios DataFrame
        """
        df = df.copy()
        logger.info("Transforming financial_ratios dataset")

        # Normalize company_id
        if "company_id" in df.columns:
            df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()

        # Normalize period
        if "period" in df.columns:
            df["period"] = df["period"].astype(str).str.strip()

        # Convert numeric columns
        numeric_cols = [
            "pe_ratio", "pb_ratio", "ps_ratio", "roe", "roa",
            "debt_to_equity", "current_ratio", "quick_ratio", "dividend_yield"
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        self.transformation_log.append({
            "dataset": "financial_ratios",
            "operations": ["normalize_ids", "convert_numeric"]
        })

        return df

    def transform_peer_groups(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform peer groups dataset.
        
        Parameters
        ----------
        df : pd.DataFrame
            Raw peer groups DataFrame
            
        Returns
        -------
        pd.DataFrame
            Transformed peer groups DataFrame
        """
        df = df.copy()
        logger.info("Transforming peer_groups dataset")

        # Normalize company_id
        if "company_id" in df.columns:
            df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()

        # Normalize peer_company_id
        if "peer_company_id" in df.columns:
            df["peer_company_id"] = df["peer_company_id"].astype(str).str.strip().str.upper()

        # Clean peer_group_name
        if "peer_group_name" in df.columns:
            df["peer_group_name"] = df["peer_group_name"].astype(str).str.strip()

        self.transformation_log.append({
            "dataset": "peer_groups",
            "operations": ["normalize_ids", "clean_strings"]
        })

        return df

    def transform_dataset(
        self,
        dataset_name: str,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Apply appropriate transformation to a dataset.
        
        Parameters
        ----------
        dataset_name : str
            Name of the dataset
        df : pd.DataFrame
            DataFrame to transform
            
        Returns
        -------
        pd.DataFrame
            Transformed DataFrame
            
        Raises
        ------
        ValueError
            If dataset_name is not recognized
        """
        transformers = {
            "companies": self.transform_companies,
            "profit_loss": self.transform_profit_loss,
            "balance_sheet": self.transform_balance_sheet,
            "cash_flow": self.transform_cash_flow,
            "analysis": self.transform_analysis,
            "documents": self.transform_documents,
            "pros_cons": self.transform_pros_cons,
            "sectors": self.transform_sectors,
            "stock_prices": self.transform_stock_prices,
            "market_cap": self.transform_market_cap,
            "financial_ratios": self.transform_financial_ratios,
            "peer_groups": self.transform_peer_groups,
        }

        if dataset_name not in transformers:
            raise ValueError(
                f"Unknown dataset: {dataset_name}. "
                f"Available transformers: {list(transformers.keys())}"
            )

        logger.info(f"Applying transformation to {dataset_name}")
        transformed_df = transformers[dataset_name](df)

        return transformed_df

    def get_transformation_log(self) -> List[Dict[str, Any]]:
        """
        Get log of all transformations performed.
        
        Returns
        -------
        List[Dict[str, Any]]
            List of transformations
        """
        return self.transformation_log

    def clear_log(self):
        """Clear transformation log."""
        self.transformation_log.clear()
        logger.info("Transformation log cleared")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def transform_dataset(dataset_name: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Convenience function to transform a dataset.
    
    Parameters
    ----------
    dataset_name : str
        Name of the dataset
    df : pd.DataFrame
        DataFrame to transform
        
    Returns
    -------
    pd.DataFrame
        Transformed DataFrame
    """
    transformer = DataTransformer()
    return transformer.transform_dataset(dataset_name, df)


# =============================================================================
# SCRIPT TEST
# =============================================================================

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)
    
    # Create sample DataFrame
    df = pd.DataFrame({
        "company_id": ["TCS", "INFY", "WIPRO"],
        "period": ["2024-Q1", "2024-Q2", "2024-Q3"],
        "revenue": ["1000", "2000", "3000"],
        "net_profit": [100.5, 200.3, 300.7]
    })
    
    transformer = DataTransformer()
    df_transformed = transformer.transform_profit_loss(df)
    
    print("\nTransformed DataFrame:")
    print(df_transformed)
    print("\nTransformation Log:")
    print(transformer.get_transformation_log())