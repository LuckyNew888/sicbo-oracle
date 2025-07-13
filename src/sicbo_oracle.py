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
from prediction_modules.hilo_predictor import HiLoPredictor # NEW: Import HiLoPredictor

# Import the ConfidenceScorer
from scorer import ConfidenceScorer 

class SicBoOracle:
    """
    The main Oracle class for Sic Bo prediction.
    It manages history, integrates various prediction modules, and provides a final prediction.
    This version incorporates more sophisticated prediction logic inspired by Baccarat Oracle v3.7.
    Updated to handle 'ไฮโล' (total 11) as a special outcome and to predict it.
    """
    def __init__(self):
        # Initialize history as an empty DataFrame with predefined columns.
        self.history: pd.DataFrame = pd.DataFrame(columns=['Die1', 'Die2', 'Die3', 'Total', 'HighLow', 'OddEven', 'Triplet'])
        
        # Store the last prediction made by the oracle.
        self.last_prediction_outcome: Optional[SicBoOutcome] = None
        self.last_prediction_source: Optional[str] = None # Source module(s) for the last prediction.

        # Logs to track predictions and actual results for accuracy calculation.
        self.prediction_log: List[Tuple[Optional[SicBoOutcome], Optional[str]]] = [] # (predicted_outcome, source_module_name)
        self.result_log: List[SicBoOutcome] = [] # Actual outcomes (e.g., 'สูง', 'ต่ำ', 'ตอง', 'ไฮโล')

        # Initialize all prediction modules.
        self.modules: Dict[str, BasePredictor] = {
            "กฎพื้นฐาน": RuleBasedPredictor(),
            "รูปแบบ H/L": PatternPredictor(),
            "เทรนด์ H/L": TrendPredictor(),             
            "รูปแบบ 2-2": TwoTwoPatternPredictor(),     
            "สไนเปอร์": SniperPatternPredictor(),       
            "Smart": SmartPredictor(),                 
            "ทำนายไฮโล": HiLoPredictor(), # NEW: Add HiLoPredictor
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
        """
        total = die1 + die2 + die3
        high_low = ''
        
        # Determine High/Low/ไฮโล based on total
        if total == 11:
            high_low = 'ไฮโล' # Special case: Total 11 is 'ไฮโล'
        elif 4 <= total <= 10:
            high_low = 'ต่ำ'
        elif 12 <= total <= 17:
            high_low = 'สูง'
        
        odd_even = 'คู่' if total % 2 == 0 else 'คี่'
        triplet = (die1 == die2 == die3)
        
        if triplet: # If it's a triplet, it overrides High/Low/ไฮโล and Odd/Even categories.
            high_low = 'ตอง'
            odd_even = 'ตอง'

        # Create a new DataFrame row for the current roll.
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

        self.result_log.append(high_low) # Log the actual High/Low outcome (can be 'ไฮโล' or 'ตอง')
        self.prediction_log.append((self.last_prediction_outcome, self.last_prediction_source)) 

        self.last_prediction_outcome = None 
        self.last_prediction_source = None

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
            # Iterate through history to test module performance.
            for i in range(self.min_history_for_prediction, len(self.history)):
                pred = module.predict(self.history.iloc[:i]) 
                actual_outcome = self.history.iloc[i]['HighLow'] # Use HighLow for evaluation

                # Special handling for HiLoPredictor accuracy
                if name == "ทำนายไฮโล":
                    if pred is not None:
                        total_predictions += 1
                        if pred == actual_outcome == 'ไฮโล': # Only count win if predicted 'ไฮโล' and actual was 'ไฮโล'
                            wins += 1
                else: # For High/Low prediction modules
                    # Only count predictions that were made and actual was not 'ตอง' or 'ไฮโล'
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
        
        # Filter history for non-'ตอง' and non-'ไฮโล' High/Low outcomes for H/L modules
        filtered_highlow_history = self.history[self.history['HighLow'].isin(['สูง', 'ต่ำ'])].copy()
        
        # Filter history for HiLo outcomes for HiLoPredictor
        filtered_hilo_history = self.history[self.history['HighLow'] == 'ไฮโล'].copy()

        if len(self.history) < lookback + self.min_history_for_prediction: # Check overall history length
            return None

        for name, module in modules.items():
            wins, total = 0, 0
            
            if name == "ทำนายไฮโล":
                # Evaluate HiLoPredictor
                for i in range(len(self.history) - lookback, len(self.history)):
                    if i < self.min_history_for_prediction: continue
                    pred = module.predict(self.history.iloc[:i])
                    actual = self.history.iloc[i]['HighLow']
                    if pred is not None:
                        total += 1
                        if pred == actual == 'ไฮโล':
                            wins += 1
            else:
                # Evaluate High/Low predictors
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
        """
        if len(self.history) < self.min_history_for_prediction:
            self.last_prediction_outcome = None
            self.last_prediction_source = None
            return None, None, None, f"⚠️ รอข้อมูลครบ {self.min_history_for_prediction} ตา ก่อนเริ่มทำนาย", 0

        current_miss_streak = self._calculate_miss_streak() 

        # Filter history for non-'ตอง' and non-'ไฮโล' High/Low outcomes for prediction readiness count
        filtered_highlow_history_for_count = [val for val in self.history['HighLow'].tolist() if val in ['สูง', 'ต่ำ']]
        high_count = filtered_highlow_history_for_count.count("สูง")
        low_count = filtered_highlow_history_for_count.count("ต่ำ")

        # "wait" condition: if not enough non-special outcome history or long miss streak
        if (high_count + low_count) < self.min_non_special_outcome_history_for_prediction or current_miss_streak >= 6:
            self.last_prediction_outcome = None
            self.last_prediction_source = None
            return None, None, None, f"⏳ กำลังวิเคราะห์ข้อมูล หรือยังไม่พบรูปแบบที่ชัดเจน (ต้องการ สูง/ต่ำ ที่ไม่ใช่ตอง/ไฮโล อย่างน้อย {self.min_non_special_outcome_history_for_prediction} ตา)", current_miss_streak

        module_predictions = {}
        for name, module in self.modules.items():
            module_predictions[name] = module.predict(self.history)

        weights = self.get_normalized_module_weights()

        # Check for a strong 'ไฮโล' prediction first
        hilo_pred = module_predictions.get("ทำนายไฮโล")
        if hilo_pred == "ไฮโล" and weights.get("ทำนายไฮโล", 0) > 0.7: # If HiLoPredictor is confident
            final_pred = "ไฮโล"
            source = "ทำนายไฮโล"
            confidence = min(int(weights.get("ทำนายไฮโล", 0.5) * 100), 95)
            pattern = None # No specific pattern for HiLo
        else:
            # Otherwise, use the scorer for High/Low prediction
            final_pred, source, confidence, pattern = self.scorer.score(module_predictions, weights, self.history)

        # Baccarat-inspired "recovery" logic: if on a miss streak, try to use the best recent module
        # This recovery logic will now also consider 'ทำนายไฮโล' if it's the best recent module.
        if current_miss_streak in [3, 4, 5]:
            recovery_modules_order = ["Smart", "สไนเปอร์", "ทำนายไฮโล", "เทรนด์ H/L", "รูปแบบ H/L", "รูปแบบ 2-2", "กฎพื้นฐาน"]
            
            for mod_name in recovery_modules_order:
                if mod_name in module_predictions and module_predictions[mod_name] is not None:
                    # If the recovery module predicts 'ไฮโล', use it.
                    if module_predictions[mod_name] == "ไฮโล":
                        final_pred = "ไฮโล"
                        source = f"{mod_name}-Recovery"
                        confidence = min(int(weights.get(mod_name, 0.5) * 100 * 1.2), 95)
                        pattern = None
                        break
                    # Otherwise, if it's a H/L prediction, use it.
                    elif module_predictions[mod_name] in ["สูง", "ต่ำ"]:
                        final_pred = module_predictions[mod_name]
                        source = f"{mod_name}-Recovery"
                        confidence = min(int(weights.get(mod_name, 0.5) * 100 * 1.2), 95) 
                        break 

        self.last_prediction_outcome = final_pred
        self.last_prediction_source = source
        
        return final_pred, source, confidence, pattern, current_miss_streak

    def _calculate_miss_streak(self) -> int:
        """
        Calculates the current streak of incorrect predictions.
        Excludes 'ตอง' and 'ไฮโล' results from counting towards the streak if the prediction was for H/L.
        If the prediction was for 'ไฮโล', it counts misses against 'ไฮโล'.
        """
        streak = 0
        for pred_tuple, actual_outcome in zip(reversed(self.prediction_log), reversed(self.result_log)):
            pred_outcome, _ = pred_tuple
            
            if pred_outcome is None: # No prediction was made for this round
                continue
            
            if pred_outcome in ["สูง", "ต่ำ"]: # If the oracle predicted High/Low
                # If actual was 'ตอง' or 'ไฮโล', it's a push/special, not a miss for H/L streak.
                if actual_outcome in ["ตอง", "ไฮโล"]:
                    continue
                # If actual was different from H/L prediction, it's a miss.
                if pred_outcome != actual_outcome:
                    streak += 1
                else: # Correct H/L prediction breaks streak
                    break
            elif pred_outcome == "ไฮโล": # If the oracle predicted 'ไฮโล'
                # If actual was 'ไฮโล', it's a win for 'ไฮโล' prediction, breaks streak.
                if actual_outcome == "ไฮโล":
                    break
                else: # If actual was anything else, it's a miss for 'ไฮโล' prediction.
                    streak += 1
            # We are not predicting 'ตอง', so no specific logic for that.
        return streak
                                                                   # src/sicbo_oracle.py
import pandas as pd
from typing import List, Optional, Tuple, Dict, Literal
import sys
import os

# Define common types for Sic Bo outcomes
SicBoOutcome = Literal["สูง", "ต่ำ", "คู่", "คี่", "ตอง", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17"]

# Import base predictor and specific prediction modules
from prediction_modules.base_predictor import BasePredictor
from prediction_modules.rule_based_predictor import RuleBasedPredictor
from prediction_modules.pattern_predictor import PatternPredictor
from prediction_modules.trend_predictor import TrendPredictor             
from prediction_modules.two_two_pattern_predictor import TwoTwoPatternPredictor 
from prediction_modules.sniper_pattern_predictor import SniperPatternPredictor 
from prediction_modules.smart_predictor import SmartPredictor             

# Import the ConfidenceScorer
from scorer import ConfidenceScorer 

class SicBoOracle:
    """
    The main Oracle class for Sic Bo prediction.
    It manages history, integrates various prediction modules, and provides a final prediction.
    This version incorporates more sophisticated prediction logic inspired by Baccarat Oracle v3.7.
    """
    def __init__(self):
        # Initialize history as an empty DataFrame with predefined columns.
        self.history: pd.DataFrame = pd.DataFrame(columns=['Die1', 'Die2', 'Die3', 'Total', 'HighLow', 'OddEven', 'Triplet'])
        
        # Store the last prediction made by the oracle.
        self.last_prediction_outcome: Optional[SicBoOutcome] = None
        self.last_prediction_source: Optional[str] = None # Source module(s) for the last prediction.

        # Logs to track predictions and actual results for accuracy calculation.
        self.prediction_log: List[Tuple[Optional[SicBoOutcome], Optional[str]]] = [] # (predicted_outcome, source_module_name)
        self.result_log: List[SicBoOutcome] = [] # Actual outcomes (e.g., 'สูง', 'ต่ำ', 'ตอง')

        # Initialize all prediction modules.
        # Each module is an instance of a class inheriting from BasePredictor.
        self.modules: Dict[str, BasePredictor] = {
            "กฎพื้นฐาน": RuleBasedPredictor(),
            "รูปแบบ H/L": PatternPredictor(),
            "เทรนด์ H/L": TrendPredictor(),             
            "รูปแบบ 2-2": TwoTwoPatternPredictor(),     
            "สไนเปอร์": SniperPatternPredictor(),       
            "Smart": SmartPredictor(),                 
        }
        # Initialize the ConfidenceScorer.
        self.scorer = ConfidenceScorer()
        
        # Minimum number of rolls required in history before the oracle starts making predictions.
        self.min_history_for_prediction = 5 
        # Minimum non-triplet High/Low outcomes needed before making predictions (similar to Baccarat's 20 P/B)
        # *** แก้ไข: ลดจำนวนตาขั้นต่ำสำหรับ High/Low ที่ไม่ใช่ตอง จาก 20 เป็น 10 ***
        self.min_non_triplet_history_for_prediction = 10 

    def add_roll(self, die1: int, die2: int, die3: int):
        """
        Adds a new Sic Bo roll outcome to the history.
        Calculates High/Low, Odd/Even, and Triplet status for the new roll.
        """
        total = die1 + die2 + die3
        high_low = ''
        if total >= 11 and total <= 17:
            high_low = 'สูง'
        elif total >= 4 and total <= 10:
            high_low = 'ต่ำ'
        
        odd_even = 'คู่' if total % 2 == 0 else 'คี่'
        triplet = (die1 == die2 == die3)
        
        if triplet: # If it's a triplet, it overrides High/Low and Odd/Even categories.
            high_low = 'ตอง'
            odd_even = 'ตอง'

        # Create a new DataFrame row for the current roll.
        new_roll = pd.DataFrame([{
            'Die1': die1, 'Die2': die2, 'Die3': die3,
            'Total': total, 'HighLow': high_low, 'OddEven': odd_even,
            'Triplet': triplet
        }])
        
        # Concatenate the new roll to the existing history.
        self.history = pd.concat([self.history, new_roll], ignore_index=True)
        
        # Keep history length manageable to prevent excessive memory usage.
        # If history exceeds 100 rolls, remove the oldest one.
        if len(self.history) > 100: 
            self.history = self.history.tail(100).reset_index(drop=True)
            if self.prediction_log: self.prediction_log.pop(0)
            if self.result_log: self.result_log.pop(0)

        # Log the actual outcome of the current roll.
        self.result_log.append(high_low) # We log the High/Low outcome for simplicity in accuracy calculation.
        # Log the prediction that was made *before* this roll occurred.
        self.prediction_log.append((self.last_prediction_outcome, self.last_prediction_source)) 

        # Reset last_prediction_outcome and source for the next prediction cycle.
        self.last_prediction_outcome = None 
        self.last_prediction_source = None

    def remove_last_roll(self):
        """Removes the last roll from history and corresponding log entries."""
        if not self.history.empty:
            self.history = self.history.iloc[:-1] # Remove the last row from DataFrame.
            if self.prediction_log: self.prediction_log.pop() # Remove last prediction log.
            if self.result_log: self.result_log.pop() # Remove last result log.

    def reset_history(self):
        """Clears all history and resets the oracle's state."""
        self.history = pd.DataFrame(columns=['Die1', 'Die2', 'Die3', 'Total', 'HighLow', 'OddEven', 'Triplet'])
        self.last_prediction_outcome = None
        self.last_prediction_source = None
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
            # Iterate through history to test module performance.
            # Start from min_history_for_prediction to ensure enough data for each module to predict.
            for i in range(self.min_history_for_prediction, len(self.history)):
                # Get prediction based on history *up to the point before the current roll*.
                # This simulates how the module would have predicted at that time.
                pred = module.predict(self.history.iloc[:i]) 
                
                # Compare with the actual outcome of the *current roll*.
                actual_outcome = self.history.iloc[i]['HighLow'] # We are evaluating High/Low predictions.

                # Only count predictions that were made and are not 'ตอง' (as 'ตอง' is an exception).
                if pred is not None and actual_outcome not in ['ตอง']: 
                    total_predictions += 1
                    if pred == actual_outcome:
                        wins += 1
            
            # Calculate accuracy percentage.
            accuracies[name] = (wins / total_predictions * 100) if total_predictions else 0
        return accuracies

    def get_normalized_module_weights(self) -> Dict[str, float]:
        """
        Normalizes module accuracies to be used as weights in the ConfidenceScorer.
        Higher accuracy modules will have higher weights.
        """
        accuracies = self.get_module_accuracies()
        if not accuracies:
            # If no accuracies are available (e.g., not enough history), default to equal weights.
            return {name: 1.0 for name in self.modules.keys()} 
        
        max_acc = max(accuracies.values())
        if max_acc == 0:
            # If all accuracies are zero, also default to equal weights.
            return {name: 1.0 for name in self.modules.keys()} 
        
        # Normalize by dividing each accuracy by the maximum accuracy.
        return {name: acc / max_acc for name, acc in accuracies.items()}
    
    def get_best_recent_module(self, lookback: int = 10) -> Optional[str]:
        """
        Identifies the best performing module based on recent history (last 'lookback' rolls).
        This is used for the 'recovery' logic.
        Adapted from Baccarat's get_best_recent_module.
        """
        modules = self.modules
        scores = {}
        
        # Filter history for non-triplet High/Low outcomes
        filtered_history = self.history[self.history['HighLow'].isin(['สูง', 'ต่ำ'])].copy()

        if len(filtered_history) < lookback + self.min_history_for_prediction:
            return None # Not enough data to assess recent performance

        # Iterate through recent history to evaluate module performance
        for name, module in modules.items():
            wins, total = 0, 0
            # Iterate through the relevant portion of filtered history
            for i in range(len(filtered_history) - lookback, len(filtered_history)):
                # Ensure enough history is available for the module to make a prediction at this point
                if i < self.min_history_for_prediction: continue 
                
                # Predict using history up to the point before the current roll
                pred = module.predict(filtered_history.iloc[:i]) 
                actual = filtered_history.iloc[i]['HighLow']

                if pred is not None:
                    total += 1
                    if pred == actual:
                        wins += 1
            
            if total > 0:
                scores[name] = wins / total
        
        # Return the name of the module with the highest recent score
        return max(scores, key=scores.get) if scores else None

    def predict_next_outcome(self) -> Tuple[Optional[SicBoOutcome], Optional[str], Optional[int], Optional[str], int]:
        """
        Calculates the next prediction based on all modules and confidence scoring.
        This is the main prediction method of the Oracle, incorporating Baccarat-like logic.
        Adapted from Baccarat's predict_next.
        """
        # Ensure enough history for basic prediction
        if len(self.history) < self.min_history_for_prediction:
            self.last_prediction_outcome = None
            self.last_prediction_source = None
            return None, None, None, "ข้อมูลยังไม่เพียงพอสำหรับการทำนาย", 0

        current_miss_streak = self._calculate_miss_streak() 

        # Filter history for non-triplet High/Low outcomes to count
        filtered_highlow_history = [val for val in self.history['HighLow'].tolist() if val in ['สูง', 'ต่ำ']]
        high_count = filtered_highlow_history.count("สูง")
        low_count = filtered_highlow_history.count("ต่ำ")

        # Baccarat-inspired "wait" condition: if not enough non-triplet history or long miss streak
        # *** แก้ไข: ใช้ 10 ตาแทน 20 ตา สำหรับการเริ่มทำนายหลัก ***
        if (high_count + low_count) < self.min_non_triplet_history_for_prediction or current_miss_streak >= 6:
            self.last_prediction_outcome = None
            self.last_prediction_source = None
            return None, None, None, "รอข้อมูลเพิ่มเติม หรือหยุดระบบชั่วคราว", current_miss_streak

        # Get predictions from all individual modules
        module_predictions = {}
        for name, module in self.modules.items():
            module_predictions[name] = module.predict(self.history)

        # Get weights for each module based on their historical performance
        weights = self.get_normalized_module_weights()

        # Use the ConfidenceScorer to aggregate predictions and get the final result
        final_pred, source, confidence, pattern = self.scorer.score(module_predictions, weights, self.history)

        # Baccarat-inspired "recovery" logic: if on a miss streak, try to use the best recent module
        if current_miss_streak in [3, 4, 5]:
            # Prioritize Smart, Sniper, Trend for recovery as they are more "strategic"
            recovery_modules_order = ["Smart", "สไนเปอร์", "เทรนด์ H/L", "รูปแบบ H/L", "รูปแบบ 2-2", "กฎพื้นฐาน"]
            
            for mod_name in recovery_modules_order:
                if mod_name in module_predictions and module_predictions[mod_name] is not None:
                    final_pred = module_predictions[mod_name]
                    source = f"{mod_name}-Recovery"
                    # Boost confidence slightly for recovery prediction
                    confidence = min(int(weights.get(mod_name, 0.5) * 100 * 1.2), 95) 
                    break # Use the first available recovery module's prediction

        # Store the final prediction made by the oracle
        self.last_prediction_outcome = final_pred
        self.last_prediction_source = source
        
        # Return the prediction details and the miss streak.
        return final_pred, source, confidence, pattern, current_miss_streak

    def _calculate_miss_streak(self) -> int:
        """
        Calculates the current streak of incorrect predictions (excluding 'ตอง' results).
        It looks backwards through the log of predictions vs. actual results.
        Adapted from Baccarat's calculate_miss_streak.
        """
        streak = 0
        # Iterate backwards through prediction_log and result_log simultaneously.
        for pred_tuple, actual_outcome in zip(reversed(self.prediction_log), reversed(self.result_log)):
            pred_outcome, _ = pred_tuple # Unpack the predicted outcome from the tuple.
            
            # Skip this round if the actual outcome was 'ตอง' or no prediction was made.
            if actual_outcome == 'ตอง' or pred_outcome is None:
                continue
            
            # If the prediction was incorrect, increment the streak.
            if pred_outcome != actual_outcome:
                streak += 1
            else:
                # If the prediction was correct, the streak is broken.
                break 
        return streak
