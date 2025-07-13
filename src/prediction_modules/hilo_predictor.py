# src/prediction_modules/hilo_predictor.py
import pandas as pd
from typing import Optional
from prediction_modules.base_predictor import BasePredictor, SicBoOutcome

class HiLoPredictor(BasePredictor):
    def predict(self, history: pd.DataFrame) -> Optional[SicBoOutcome]:
        """
        Predicts 'ไฮโล' (total 11) based on simple rules.
        This is a basic 'due' strategy or pattern recognition for 11.
        """
        # We need enough history to check for recent 'ไฮโล' occurrences
        if len(history) < 10: # Needs at least 10 rolls to check if 11 is 'due'
            return None
        
        # Get the last 15 non-'ตอง' outcomes
        # We include 'สูง', 'ต่ำ', 'ไฮโล' in this history to see if 'ไฮโล' is missing
        relevant_history = [val for val in history['HighLow'].tail(15).tolist() if val != 'ตอง']

        # Simple strategy: If 'ไฮโล' hasn't appeared in the last 10 relevant outcomes, predict it.
        # This is a 'due' strategy, highly speculative but provides a prediction.
        if len(relevant_history) >= 10 and 'ไฮโล' not in relevant_history[-10:]:
            return 'ไฮโล'
            
        # Another simple rule: if the last few results are very mixed, it might indicate 11.
        # This is more speculative. Let's stick to the 'due' strategy for simplicity and clarity.
        
        return None

    @property
    def name(self) -> str:
        return "ทำนายไฮโล"
