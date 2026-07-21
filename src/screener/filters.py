"""
filters.py

Filter operators and conditions for the Investment Screener Engine (Module 6).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


# =============================================================================
# FILTER OPERATORS
# =============================================================================

class FilterOperator(str, Enum):
    """
    Supported filter operators for screening.
    """

    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    EQUAL = "="
    NOT_EQUAL = "!="
    BETWEEN = "BETWEEN"
    IN = "IN"
    NOT_IN = "NOT IN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"


# =============================================================================
# FILTER CONDITION
# =============================================================================

@dataclass
class FilterCondition:
    """
    Represents a single filter condition.

    Attributes
    ----------
    field : str
        The field name to filter on (e.g., "roe", "pe_ratio")
    operator : FilterOperator
        The comparison operator
    value : Any, optional
        The value to compare against (not needed for IS NULL / IS NOT NULL)
    value2 : Any, optional
        Second value for BETWEEN operator
    """

    field: str
    operator: FilterOperator
    value: Optional[Any] = None
    value2: Optional[Any] = None

    def __post_init__(self):
        """Validate the filter condition after initialization."""
        # Convert string operator to enum if needed
        if isinstance(self.operator, str):
            try:
                self.operator = FilterOperator(self.operator)
            except ValueError:
                raise ValueError(
                    f"Invalid operator: {self.operator}. "
                    f"Must be one of: {[op.value for op in FilterOperator]}"
                )

        # Validate operator-specific requirements
        if self.operator in (FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL):
            # These operators don't need values
            return

        if self.operator == FilterOperator.BETWEEN:
            if self.value is None or self.value2 is None:
                raise ValueError(
                    "BETWEEN operator requires both 'value' and 'value2' parameters"
                )
            if self.value >= self.value2:
                raise ValueError(
                    f"BETWEEN operator requires value < value2, got {self.value} >= {self.value2}"
                )
        elif self.operator in (FilterOperator.IN, FilterOperator.NOT_IN):
            if self.value is None:
                raise ValueError(f"{self.operator.value} operator requires a list of values")
            if not isinstance(self.value, (list, tuple)):
                raise ValueError(
                    f"{self.operator.value} operator requires a list or tuple, got {type(self.value)}"
                )
        else:
            if self.value is None:
                raise ValueError(f"{self.operator.value} operator requires a value")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert filter condition to dictionary.

        Returns
        -------
        Dict[str, Any]
            Dictionary representation of the filter condition
        """
        result = {
            "field": self.field,
            "operator": self.operator.value,
            "value": self.value,
        }
        if self.value2 is not None:
            result["value2"] = self.value2
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FilterCondition":
        """
        Create FilterCondition from dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Dictionary with filter condition data

        Returns
        -------
        FilterCondition
            FilterCondition instance
        """
        return cls(
            field=data["field"],
            operator=data["operator"],
            value=data.get("value"),
            value2=data.get("value2"),
        )


# =============================================================================
# FILTER GROUP (for AND/OR logic)
# =============================================================================

@dataclass
class FilterGroup:
    """
    Represents a group of filter conditions with AND/OR logic.

    Attributes
    ----------
    conditions : List[Union[FilterCondition, FilterGroup]]
        List of conditions or nested groups
    logic : str
        Logic operator: "AND" or "OR"
    """

    conditions: List[Union[FilterCondition, "FilterGroup"]]
    logic: str = "AND"

    def __post_init__(self):
        """Validate the filter group."""
        if self.logic not in ("AND", "OR"):
            raise ValueError(f"Filter group logic must be 'AND' or 'OR', got '{self.logic}'")

        if not self.conditions:
            raise ValueError("Filter group must have at least one condition")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert filter group to dictionary.

        Returns
        -------
        Dict[str, Any]
            Dictionary representation of the filter group
        """
        return {
            "logic": self.logic,
            "conditions": [cond.to_dict() for cond in self.conditions],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FilterGroup":
        """
        Create FilterGroup from dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Dictionary with filter group data

        Returns
        -------
        FilterGroup
            FilterGroup instance
        """
        conditions = []
        for cond_data in data["conditions"]:
            if "conditions" in cond_data:
                # Nested group
                conditions.append(FilterGroup.from_dict(cond_data))
            else:
                # Simple condition
                conditions.append(FilterCondition.from_dict(cond_data))

        return cls(conditions=conditions, logic=data.get("logic", "AND"))


# =============================================================================
# FILTER VALIDATOR
# =============================================================================

class FilterValidator:
    """
    Validates filter conditions against available data fields.
    """

    def __init__(self, valid_fields: Dict[str, Dict[str, str]]):
        """
        Initialize filter validator.

        Parameters
        ----------
        valid_fields : Dict[str, Dict[str, str]]
            Dictionary of valid field names and their metadata
        """
        self.valid_fields = valid_fields

    def validate_field(self, field: str) -> bool:
        """
        Check if a field is valid for screening.

        Parameters
        ----------
        field : str
            Field name to validate

        Returns
        -------
        bool
            True if field is valid
        """
        return field in self.valid_fields

    def validate_operator(self, operator: Union[str, FilterOperator]) -> bool:
        """
        Check if an operator is valid.

        Parameters
        ----------
        operator : Union[str, FilterOperator]
            Operator to validate

        Returns
        -------
        bool
            True if operator is valid
        """
        if isinstance(operator, str):
            try:
                FilterOperator(operator)
                return True
            except ValueError:
                return False
        return isinstance(operator, FilterOperator)

    def validate_filter(self, filter_condition: FilterCondition) -> List[str]:
        """
        Validate a filter condition and return list of errors.

        Parameters
        ----------
        filter_condition : FilterCondition
            Filter condition to validate

        Returns
        -------
        List[str]
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate field
        if not self.validate_field(filter_condition.field):
            errors.append(
                f"Invalid field: '{filter_condition.field}'. "
                f"Valid fields: {list(self.valid_fields.keys())}"
            )

        # Validate operator
        if not self.validate_operator(filter_condition.operator):
            errors.append(
                f"Invalid operator: '{filter_condition.operator}'. "
                f"Valid operators: {[op.value for op in FilterOperator]}"
            )

        # Validate value for operators that require it
        if filter_condition.operator not in (
            FilterOperator.IS_NULL,
            FilterOperator.IS_NOT_NULL,
        ):
            if filter_condition.value is None:
                errors.append(f"Operator {filter_condition.operator.value} requires a value")

        return errors

    def validate_filter_group(self, filter_group: FilterGroup) -> List[str]:
        """
        Validate a filter group and return list of errors.

        Parameters
        ----------
        filter_group : FilterGroup
            Filter group to validate

        Returns
        -------
        List[str]
            List of validation errors (empty if valid)
        """
        errors = []

        for condition in filter_group.conditions:
            if isinstance(condition, FilterCondition):
                errors.extend(self.validate_filter(condition))
            elif isinstance(condition, FilterGroup):
                errors.extend(self.validate_filter_group(condition))

        return errors