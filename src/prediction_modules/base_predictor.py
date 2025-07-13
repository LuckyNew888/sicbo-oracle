# src/prediction_modules/base_predictor.py
from abc import ABC, abstractmethod
from typing import List, Optional, Literal
import pandas as pd

# Define common types for Sic Bo outcomes
# We use 'สูง', 'ต่ำ', 'คู่', 'คี่', 'ตอง'
# Or 'Total' for specific total scores (though modules might predict H/L/Odd/Even primarily)
SicBoOutcome = Literal["สูง", "ต่ำ", "คู่", "คี่", "ตอง", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17"]

class BasePredictor(ABC):
    """Abstract Base Class for all Sic Bo prediction modules."""

    @abstractmethod
    def predict(self, history: pd.DataFrame) -> Optional[SicBoOutcome]:
        """
        Makes a prediction based on the history of Sic Bo outcomes.
        
        Args:
            history (pd.DataFrame): A DataFrame containing the history of Sic Bo rolls.
                                     (e.g., from data_generator, with 'HighLow', 'OddEven', 'Total', 'Triplet' columns)

        Returns:
            Optional[SicBoOutcome]: The predicted outcome ('สูง', 'ต่ำ', etc.) or None if no prediction can be made.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the name of the prediction module."""
        pass
