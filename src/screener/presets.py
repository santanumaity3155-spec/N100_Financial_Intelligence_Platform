"""
presets.py

Preset screener definitions for the Investment Screener Engine (Module 6).
"""

from typing import Any, Dict, List

from .constants import PRESET_SCREENERS


def get_preset_screener(preset_id: str) -> Dict[str, Any]:
    """
    Get a preset screener definition by ID.

    Parameters
    ----------
    preset_id : str
        Preset screener identifier (e.g., "value_investing", "growth_investing")

    Returns
    -------
    Dict[str, Any]
        Preset screener definition

    Raises
    ------
    ValueError
        If preset_id is not found
    """
    if preset_id not in PRESET_SCREENERS:
        available = list(PRESET_SCREENERS.keys())
        raise ValueError(
            f"Unknown preset screener: '{preset_id}'. "
            f"Available presets: {available}"
        )

    return PRESET_SCREENERS[preset_id]


def list_preset_screeners() -> List[Dict[str, Any]]:
    """
    List all available preset screeners.

    Returns
    -------
    List[Dict[str, Any]]
        List of preset screener definitions with id, name, and description
    """
    return [
        {
            "id": preset_id,
            "name": preset_def["name"],
            "description": preset_def["description"],
            "filter_count": len(preset_def.get("filters", [])),
        }
        for preset_id, preset_def in PRESET_SCREENERS.items()
    ]


def validate_preset_screener(preset_id: str) -> Dict[str, Any]:
    """
    Validate a preset screener definition.

    Parameters
    ----------
    preset_id : str
        Preset screener identifier

    Returns
    -------
    Dict[str, Any]
        Validation result with 'valid' flag and any errors
    """
    try:
        preset = get_preset_screener(preset_id)
    except ValueError as e:
        return {"valid": False, "errors": [str(e)]}

    errors = []

    # Validate filters
    filters = preset.get("filters", [])
    if not filters:
        errors.append("Preset screener has no filters defined")

    for i, filter_def in enumerate(filters):
        if "field" not in filter_def:
            errors.append(f"Filter {i}: missing 'field'")
        if "operator" not in filter_def:
            errors.append(f"Filter {i}: missing 'operator'")
        if "value" not in filter_def and filter_def.get("operator") not in (
            "IS NULL",
            "IS NOT NULL",
        ):
            errors.append(f"Filter {i}: missing 'value'")

    # Validate sort configuration
    if "sort_by" in preset:
        sort_by = preset["sort_by"]
        # Note: We don't validate against VALID_SCREEN_FIELDS here because
        # preset screeners may use fields from different tables

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "preset_id": preset_id,
        "name": preset.get("name"),
    }


# =============================================================================
# PRESET SCREENER CATEGORIES
# =============================================================================

PRESET_CATEGORIES = {
    "Value": ["value_investing", "undervalued"],
    "Growth": ["growth_investing", "momentum"],
    "Income": ["dividend_investing"],
    "Quality": ["high_roe", "quality", "blue_chip", "healthy_companies"],
    "Balance Sheet": ["low_debt"],
}


def get_presets_by_category(category: str) -> List[str]:
    """
    Get preset screener IDs by category.

    Parameters
    ----------
    category : str
        Category name (e.g., "Value", "Growth", "Quality")

    Returns
    -------
    List[str]
        List of preset screener IDs in the category
    """
    return PRESET_CATEGORIES.get(category, [])


def list_all_categories() -> List[str]:
    """
    List all available preset categories.

    Returns
    -------
    List[str]
        List of category names
    """
    return list(PRESET_CATEGORIES.keys())