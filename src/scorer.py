# src/scorer.py
from typing import Dict, List, Optional, Tuple
import pandas as pd
# *** แก้ไข: เปลี่ยน Relative Import เป็น Absolute Import ***
from prediction_modules.base_predictor import SicBoOutcome

class ConfidenceScorer:
    def score(self, 
              predictions: Dict[str, Optional[SicBoOutcome]], 
              weights: Dict[str, float], 
              history: pd.DataFrame) -> Tuple[Optional[SicBoOutcome], Optional[str], Optional[int], Optional[str]]:
        """
        Aggregates predictions from multiple modules, applies weights, and determines the best prediction.
        Adapted from Baccarat's ConfidenceScorer.

        Args:
            predictions (Dict[str, Optional[SicBoOutcome]]): Dictionary of module_name: prediction_outcome.
            weights (Dict[str, float]): Dictionary of module_name: weight (e.g., accuracy).
            history (pd.DataFrame): The full history DataFrame for pattern extraction.

        Returns:
            Tuple[Optional[SicBoOutcome], Optional[str], Optional[int], Optional[str]]:
            - Best predicted outcome
            - Name of the module that provided the strongest support
            - Confidence score (0-100)
            - Identified pattern (e.g., "HLHL", "HHH")
        """
        
        # Initialize scores for main outcomes (High/Low).
        # This scorer primarily focuses on High/Low predictions for aggregation.
        total_score_high_low = {"สูง": 0.0, "ต่ำ": 0.0}

        # Collect all valid predictions and apply their respective weights.
        for name, pred in predictions.items():
            if pred is None: # Skip if a module didn't make a prediction.
                continue
            
            weight = weights.get(name, 0.5) # Get the weight for the current module, default to 0.5.

            # Aggregate scores based on prediction type.
            if pred in ["สูง", "ต่ำ"]:
                total_score_high_low[pred] += weight
            # You can extend this to include 'คู่'/'คี่' or 'แต้มรวม' if desired.

        best_overall_prediction: Optional[SicBoOutcome] = None
        best_source: Optional[str] = None
        overall_confidence: Optional[int] = None
        
        # Determine the best High/Low prediction based on aggregated scores.
        sum_hl = sum(total_score_high_low.values())
        if sum_hl > 0: # Only proceed if there are High/Low predictions.
            best_hl = max(total_score_high_low, key=total_score_high_low.get)
            conf_hl = int((total_score_high_low[best_hl] / sum_hl) * 100)
            
            if conf_hl > 0: # Even 0 confidence can be a prediction if it's the only one
                best_overall_prediction = best_hl
                overall_confidence = min(conf_hl, 95) # Cap confidence at 95% for realism.
                # Identify the source module(s) that contributed to this best prediction.
                source_modules = [name for name, pred in predictions.items() if pred == best_hl]
                best_source = ", ".join(source_modules)

        # Extract a relevant pattern for display in the UI.
        identified_pattern = self._extract_dominant_pattern(history)

        return best_overall_prediction, best_source, overall_confidence, identified_pattern

    def _extract_dominant_pattern(self, history: pd.DataFrame) -> Optional[str]:
        """
        Attempts to extract a visually recognizable pattern from the recent history,
        returning a short code string that can be mapped to a user-friendly name in app.py.
        Adapted from Baccarat's extract_pattern.
        """
        if len(history) < 6: # Needs enough history to detect patterns.
            return None
        
        # Filter history to only include 'สูง' or 'ต่ำ' for pattern detection.
        recent_highlow_filtered = [val for val in history['HighLow'].tail(6).tolist() if val in ['สูง', 'ต่ำ']]
        
        if len(recent_highlow_filtered) < 4: # Need at least 4 non-triplet results for common patterns.
            return None

        # Convert the list of outcomes to a string for easy pattern matching.
        pattern_str = "".join(recent_highlow_filtered)

        # Map to short codes that match the pattern_name_map in app.py.
        # These are common patterns in Baccarat/Sic Bo.
        if "สูงต่ำสูงต่ำ" in pattern_str: return "HLHL" # Ping Pong (High-Low-High-Low)
        if "ต่ำสูงต่ำสูง" in pattern_str: return "LHLH" # Ping Pong (Low-High-Low-High)
        if "สูงสูงต่ำต่ำ" in pattern_str: return "HHL_LL" # 2-Cut (High-High-Low-Low)
        if "ต่ำต่ำสูงสูง" in pattern_str: return "LLH_HH" # 2-Cut (Low-Low-High-High)
        
        # Check for consecutive "Dragon" patterns (3 or more consecutive).
        if pattern_str.endswith("สูงสูงสูง"): return "HHH" # Dragon High
        if pattern_str.endswith("ต่ำต่ำต่ำ"): return "LLL" # Dragon Low
        
        return None
