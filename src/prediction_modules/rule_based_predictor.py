# src/prediction_modules/rule_based_predictor.py
import pandas as pd
from typing import Optional
from .base_predictor import BasePredictor, SicBoOutcome

class RuleBasedPredictor(BasePredictor):
    def predict(self, history: pd.DataFrame) -> Optional[SicBoOutcome]:
        """
        Predicts based on simple rules like consecutive outcomes.
        Adapted from Baccarat's RuleEngine.
        """
        if len(history) < 3:
            return None
        
        # Extract last 3 HighLow and OddEven outcomes from the DataFrame
        last_three_highlow = history['HighLow'].tail(3).tolist()
        last_three_odd_even = history['OddEven'].tail(3).tolist()

        # Rule 1: Three consecutive High/Low (excluding triplets)
        # If the last three are the same and not 'ตอง', predict the opposite.
        if (last_three_highlow[0] != 'ตอง' and 
            last_three_highlow[0] == last_three_highlow[1] == last_three_highlow[2]):
            return 'ต่ำ' if last_three_highlow[-1] == 'สูง' else 'สูง'
        
        # Rule 2: Three consecutive Odd/Even (excluding triplets)
        # If the last three are the same and not 'ตอง', predict the opposite.
        if (last_three_odd_even[0] != 'ตอง' and 
            last_three_odd_even[0] == last_three_odd_even[1] == last_three_odd_even[2]):
            return 'คี่' if last_three_odd_even[-1] == 'คู่' else 'คู่'

        # Rule 3: Alternating pattern (e.g., H-L-H or L-H-L)
        # If the last three are alternating and not 'ตอง', predict the last outcome.
        if (last_three_highlow[0] != 'ตอง' and 
            last_three_highlow[0] != last_three_highlow[1] and 
            last_three_highlow[1] != last_three_highlow[2]):
            return last_three_highlow[-1] # Predict the same as the last one in alternating sequence

        return None

    @property
    def name(self) -> str:
        return "กฎพื้นฐาน"
