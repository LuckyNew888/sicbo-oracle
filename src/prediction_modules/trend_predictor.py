# src/prediction_modules/trend_predictor.py
import pandas as pd
from typing import Optional
# *** แก้ไข: เปลี่ยน Relative Import เป็น Absolute Import ***
from prediction_modules.base_predictor import BasePredictor, SicBoOutcome

class TrendPredictor(BasePredictor):
    def predict(self, history: pd.DataFrame) -> Optional[SicBoOutcome]:
        """
        Predicts based on the dominant trend (High or Low) in the recent history.
        Adapted from Baccarat's TrendScanner.
        """
        if len(history) < 10: # Needs at least 10 rolls for trend analysis
            return None
        
        # Get the last 10 non-triplet High/Low outcomes
        last_ten_highlow = [val for val in history['HighLow'].tail(10).tolist() if val != 'ตอง']

        if len(last_ten_highlow) < 5: # Need a reasonable number of non-triplet outcomes for a reliable trend
            return None

        high_count = last_ten_highlow.count("สูง")
        low_count = last_ten_highlow.count("ต่ำ")

        # If one outcome is significantly more frequent (e.g., > 6 out of 10 non-triplets)
        if high_count > 6:
            return "สูง"
        if low_count > 6:
            return "ต่ำ"
        
        return None

    @property
    def name(self) -> str:
        return "เทรนด์ H/L"
