# src/sicbo_oracle.py
import pandas as pd
from typing import List, Optional, Tuple, Dict, Literal
import sys
import os

# Define common types for Sic Bo outcomes
SicBoOutcome = Literal["สูง", "ต่ำ", "คู่", "คี่", "ตอง", "ไฮโล", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17"]

# Import base predictor and specific prediction modules
from prediction_modules.base_predictor import BasePredictor
from prediction_modules.rule_based_predictor import RuleBasedPredictor
from prediction_modules.pattern_predictor import PatternPredictor
from prediction_modules.trend_predictor import TrendPredictor             
from prediction_modules.two_two_pattern_predictor import TwoTwoPatternPredictor 
from prediction_modules.sniper_pattern_predictor import SniperPatternPredictor 
from prediction_modules.smart_predictor import SmartPredictor             
from prediction_modules.hilo_predictor import HiLoPredictor 

# Import the ConfidenceScorer
from scorer import ConfidenceScorer 

class SicBoOracle:
    """
    The main Oracle class for Sic Bo prediction.
    It manages history, integrates various prediction modules, and provides a final prediction.
    This version incorporates more sophisticated prediction logic inspired by Baccarat Oracle v3.7.
    Updated to handle 'ไฮโล' (total 11) as a special outcome and to predict it.
    Also, improved miss streak calculation logic.
    """
    def __init__(self):
        # Initialize history as an empty DataFrame with predefined columns.
        self.history: pd.DataFrame = pd.DataFrame(columns=['Die1', 'Die2', 'Die3', 'Total', 'HighLow', 'OddEven', 'Triplet'])
        
        # Store the last prediction made by the oracle.
        self.last_prediction_outcome: Optional[SicBoOutcome] = None
        self.last_prediction_source: Optional[str] = None 
        self.last_prediction_type: Literal["normal", "recovery", "none"] = "none" # NEW: Track prediction type

        # Logs to track predictions and actual results for accuracy calculation.
        # prediction_log now stores (predicted_outcome, source_module_name, prediction_type)
        self.prediction_log: List[Tuple[Optional[SicBoOutcome], Optional[str], Literal["normal", "recovery", "none"]]] = [] 
        self.result_log: List[SicBoOutcome] = [] 

        # Initialize all prediction modules.
        self.modules: Dict[str, BasePredictor] = {
            "กฎพื้นฐาน": RuleBasedPredictor(),
            "รูปแบบ H/L": PatternPredictor(),
            "เทรนด์ H/L": TrendPredictor(),             
            "รูปแบบ 2-2": TwoTwoPatternPredictor(),     
            "สไนเปอร์": SniperPatternPredictor(),       
            "Smart": SmartPredictor(),                 
            "ทำนายไฮโล": HiLoPredictor(), 
        }
        # Initialize the ConfidenceScorer.
        self.scorer = ConfidenceScorer()
        
        # Minimum number of rolls required in history before the oracle starts making predictions.
        self.min_history_for_prediction = 5 
        # Minimum non-'ตอง' and non-'ไฮโล' High/Low outcomes needed before making primary H/L predictions.
        self.min_non_special_outcome_history_for_prediction = 10 

    def add_roll(self, die1: int, die2: int, die3: int):
        """
        Adds a new Sic Bo roll outcome to the history.
        Calculates High/Low, Odd/Even, and Triplet status for the new roll, including 'ไฮโล'.
        Logs the prediction made *before* this roll and the actual result.
        """
        total = die1 + die2 + die3
        high_low = ''
        
        if total == 11:
            high_low = 'ไฮโล' 
        elif 4 <= total <= 10:
            high_low = 'ต่ำ'
        elif 12 <= total <= 17:
            high_low = 'สูง'
        
        odd_even = 'คู่' if total % 2 == 0 else 'คี่'
        triplet = (die1 == die2 == die3)
        
        if triplet: 
            high_low = 'ตอง'
            odd_even = 'ตอง'

        new_roll = pd.DataFrame([{
            'Die1': die1, 'Die2': die2, 'Die3': die3,
            'Total': total, 'HighLow': high_low, 'OddEven': odd_even,
            'Triplet': triplet
        }])
        
        self.history = pd.concat([self.history, new_roll], ignore_index=True)
        
        if len(self.history) > 100: 
            self.history = self.history.tail(100).reset_index(drop=True)
            if self.prediction_log: self.prediction_log.pop(0)
            if self.result_log: self.result_log.pop(0)

        self.result_log.append(high_low) 
        # Log the prediction made *before* this roll occurred, along with its type
        self.prediction_log.append((self.last_prediction_outcome, self.last_prediction_source, self.last_prediction_type)) 

        # Reset last_prediction_outcome and source/type for the next prediction cycle.
        self.last_prediction_outcome = None 
        self.last_prediction_source = None
        self.last_prediction_type = "none" # Reset to 'none' by default for the next cycle

    def remove_last_roll(self):
        """Removes the last roll from history and corresponding log entries."""
        if not self.history.empty:
            self.history = self.history.iloc[:-1]
            if self.prediction_log: self.prediction_log.pop()
            if self.result_log: self.result_log.pop()

    def reset_history(self):
        """Clears all history and resets the oracle's state."""
        self.history = pd.DataFrame(columns=['Die1', 'Die2', 'Die3', 'Total', 'HighLow', 'OddEven', 'Triplet'])
        self.last_prediction_outcome = None
        self.last_prediction_source = None
        self.last_prediction_type = "none"
        self.prediction_log.clear()
        self.result_log.clear()

    def get_module_accuracies(self) -> Dict[str, float]:
        """
        Calculates the accuracy (win rate) for each individual prediction module
        based on the historical data.
        """
        accuracies = {}
        for name, module in self.modules.items():
            wins = 0
            total_predictions = 0
            for i in range(self.min_history_for_prediction, len(self.history)):
                pred = module.predict(self.history.iloc[:i]) 
                actual_outcome = self.history.iloc[i]['HighLow']

                if name == "ทำนายไฮโล":
                    if pred is not None:
                        total_predictions += 1
                        if pred == actual_outcome == 'ไฮโล':
                            wins += 1
                else: 
                    if pred is not None and actual_outcome not in ['ตอง', 'ไฮโล']: 
                        total_predictions += 1
                        if pred == actual_outcome:
                            wins += 1
            
            accuracies[name] = (wins / total_predictions * 100) if total_predictions else 0
        return accuracies

    def get_normalized_module_weights(self) -> Dict[str, float]:
        """
        Normalizes module accuracies to be used as weights in the ConfidenceScorer.
        """
        accuracies = self.get_module_accuracies()
        if not accuracies:
            return {name: 1.0 for name in self.modules.keys()} 
        
        max_acc = max(accuracies.values())
        if max_acc == 0:
            return {name: 1.0 for name in self.modules.keys()} 
        
        return {name: acc / max_acc for name, acc in accuracies.items()}
    
    def get_best_recent_module(self, lookback: int = 10) -> Optional[str]:
        """
        Identifies the best performing module based on recent history.
        Filters history for non-'ตอง' and non-'ไฮโล' High/Low outcomes for H/L modules.
        Evaluates HiLoPredictor separately.
        """
        modules = self.modules
        scores = {}
        
        filtered_highlow_history = self.history[self.history['HighLow'].isin(['สูง', 'ต่ำ'])].copy()
        
        if len(self.history) < lookback + self.min_history_for_prediction: 
            return None

        for name, module in modules.items():
            wins, total = 0, 0
            
            if name == "ทำนายไฮโล":
                for i in range(len(self.history) - lookback, len(self.history)):
                    if i < self.min_history_for_prediction: continue
                    pred = module.predict(self.history.iloc[:i])
                    actual = self.history.iloc[i]['HighLow']
                    if pred is not None:
                        total += 1
                        if pred == actual == 'ไฮโล':
                            wins += 1
            else:
                for i in range(len(filtered_highlow_history) - lookback, len(filtered_highlow_history)):
                    if i < self.min_history_for_prediction: continue 
                    pred = module.predict(filtered_highlow_history.iloc[:i]) 
                    actual = filtered_highlow_history.iloc[i]['HighLow']

                    if pred is not None:
                        total += 1
                        if pred == actual:
                            wins += 1
            
            if total > 0:
                scores[name] = wins / total
        
        return max(scores, key=scores.get) if scores else None

    def predict_next_outcome(self) -> Tuple[Optional[SicBoOutcome], Optional[str], Optional[int], Optional[str], int]:
        """
        Calculates the next prediction based on all modules and confidence scoring.
        Prioritizes 'ไฮโล' prediction if the HiLoPredictor gives a strong signal.
        Determines and stores the prediction type (normal, recovery, none).
        """
        current_miss_streak = self._calculate_miss_streak() 

        # Check for initial history requirement
        if len(self.history) < self.min_history_for_prediction:
            self.last_prediction_outcome = None
            self.last_prediction_source = None
            self.last_prediction_type = "none" 
            return None, None, None, f"⚠️ รอข้อมูลครบ {self.min_history_for_prediction} ตา ก่อนเริ่มทำนาย", 0

        # Filter history for non-'ตอง' and non-'ไฮโล' High/Low outcomes for prediction readiness count
        filtered_highlow_history_for_count = [val for val in self.history['HighLow'].tolist() if val in ['สูง', 'ต่ำ']]
        high_count = filtered_highlow_history_for_count.count("สูง")
        low_count = filtered_highlow_history_for_count.count("ต่ำ")

        # "wait" condition: if not enough non-special outcome history or long miss streak
        if (high_count + low_count) < self.min_non_special_outcome_history_for_prediction or current_miss_streak >= 6:
            self.last_prediction_outcome = None
            self.last_prediction_source = None
            self.last_prediction_type = "none" 
            return None, None, None, f"⏳ กำลังวิเคราะห์ข้อมูล หรือยังไม่พบรูปแบบที่ชัดเจน (ต้องการ สูง/ต่ำ ที่ไม่ใช่ตอง/ไฮโล อย่างน้อย {self.min_non_special_outcome_history_for_prediction} ตา)", current_miss_streak

        module_predictions = {}
        for name, module in self.modules.items():
            module_predictions[name] = module.predict(self.history)

        weights = self.get_normalized_module_weights()

        final_pred: Optional[SicBoOutcome] = None
        source: Optional[str] = None
        confidence: Optional[int] = None
        pattern: Optional[str] = None
        prediction_type: Literal["normal", "recovery"] = "normal" # Default to normal

        # Check for a strong 'ไฮโล' prediction first
        hilo_pred = module_predictions.get("ทำนายไฮโล")
        if hilo_pred == "ไฮโล" and weights.get("ทำนายไฮโล", 0) > 0.7: 
            final_pred = "ไฮโล"
            source = "ทำนายไฮโล"
            confidence = min(int(weights.get("ทำนายไฮโล", 0.5) * 100), 95)
            pattern = None
        else:
            # Otherwise, use the scorer for High/Low prediction
            final_pred, source, confidence, pattern = self.scorer.score(module_predictions, weights, self.history)

        # Baccarat-inspired "recovery" logic: if on a miss streak, try to use the best recent module
        # This recovery logic will now also consider 'ทำนายไฮโล' if it's the best recent module.
        if current_miss_streak in [3, 4, 5]:
            prediction_type = "recovery" # Set type to recovery if in this state
            recovery_modules_order = ["Smart", "สไนเปอร์", "ทำนายไฮโล", "เทรนด์ H/L", "รูปแบบ H/L", "รูปแบบ 2-2", "กฎพื้นฐาน"]
            
            for mod_name in recovery_modules_order:
                if mod_name in module_predictions and module_predictions[mod_name] is not None:
                    if module_predictions[mod_name] == "ไฮโล":
                        final_pred = "ไฮโล"
                        source = f"{mod_name}-Recovery"
                        confidence = min(int(weights.get(mod_name, 0.5) * 100 * 1.2), 95)
                        pattern = None
                        break
                    elif module_predictions[mod_name] in ["สูง", "ต่ำ"]:
                        final_pred = module_predictions[mod_name]
                        source = f"{mod_name}-Recovery"
                        confidence = min(int(weights.get(mod_name, 0.5) * 100 * 1.2), 95) 
                        break 

        # Store the final prediction made by the oracle for the next add_roll cycle
        self.last_prediction_outcome = final_pred
        self.last_prediction_source = source
        self.last_prediction_type = prediction_type # Store the determined prediction type
        
        return final_pred, source, confidence, pattern, current_miss_streak

    def _calculate_miss_streak(self) -> int:
        """
        Calculates the current streak of incorrect predictions based on prediction type.
        - 'none' predictions are skipped.
        - 'normal' predictions: hit resets streak, miss increments.
        - 'recovery' predictions: hit does NOT reset streak, miss increments.
        """
        print(f"DEBUG: _calculate_miss_streak called. Current prediction_log length: {len(self.prediction_log)}")
        streak = 0
        # Iterate backwards through prediction_log and result_log simultaneously.
        for i, (log_entry, actual_outcome) in enumerate(zip(reversed(self.prediction_log), reversed(self.result_log))):
            pred_outcome, _, prediction_type = log_entry # Unpack prediction_type
            print(f"DEBUG: Processing round {len(self.prediction_log) - 1 - i}: Pred={pred_outcome}, Actual={actual_outcome}, Type={prediction_type}")

            if prediction_type == "none":
                print("DEBUG:   Skipping 'none' prediction type.")
                continue # Skip rounds where no prediction was made

            # If a prediction was made (normal or recovery)
            if pred_outcome in ["สูง", "ต่ำ", "ไฮโล"]: # Check against all possible predictions
                # Special outcomes ('ตอง') are always skipped if actual.
                # If the prediction was H/L, and actual was 'ตอง' or 'ไฮโล', it's a special case, not a miss or win for H/L streak.
                if pred_outcome in ["สูง", "ต่ำ"] and actual_outcome in ["ตอง", "ไฮलो"]:
                    print("DEBUG:   Skipping H/L prediction vs Triplet/HiLo actual (special case).")
                    continue 
                
                if pred_outcome != actual_outcome:
                    streak += 1 # Miss: increment streak
                    print(f"DEBUG:   Miss! Streak incremented to {streak}.")
                else: # Hit: Check prediction type to decide if streak resets
                    print(f"DEBUG:   Hit! Prediction Type: {prediction_type}")
                    if prediction_type == "normal":
                        print("DEBUG:   Normal hit. Resetting streak and breaking.")
                        break # Reset streak on normal win
                    else: # prediction_type == "recovery" and it was a win
                        print("DEBUG:   Recovery hit. Not resetting streak, continuing to look back.")
                        continue # Do not reset streak, but also do not increment. Just pass through.
            else: # This case should ideally not be reached if pred_outcome is always one of the SicBoOutcome types
                print(f"DEBUG:   Unexpected prediction outcome: {pred_outcome}. Skipping.")
                continue
        print(f"DEBUG: _calculate_miss_streak returning {streak}")
        return streak
