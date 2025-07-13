# src/data_generator.py
import random
import pandas as pd
import os

def simulate_sicbo(num_rolls: int) -> pd.DataFrame:
    """
    Simulates a given number of Sic Bo rolls and returns a DataFrame.
    Updated to include 'ไฮโล' (Hi-Lo) for a total of 11.

    Args:
        num_rolls (int): The number of rolls to simulate.

    Returns:
        pd.DataFrame: A DataFrame containing the simulated roll data.
                      Columns: 'Die1', 'Die2', 'Die3', 'Total', 'HighLow', 'OddEven', 'Triplet'
    """
    results = []
    for _ in range(num_rolls):
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        die3 = random.randint(1, 6)
        total = die1 + die2 + die3
        
        # Determine High/Low/ไฮโล
        high_low = ''
        if total == 11:
            high_low = 'ไฮโล' # Special case for total 11
        elif total >= 12 and total <= 17: # 'สูง' is now 12-17
            high_low = 'สูง'
        elif total >= 4 and total <= 10: # 'ต่ำ' is now 4-10
            high_low = 'ต่ำ'
        
        # Determine Odd/Even
        odd_even = 'คู่' if total % 2 == 0 else 'คี่'
        
        # Determine Triplet
        triplet = False
        if die1 == die2 == die3:
            triplet = True
            high_low = 'ตอง' # Triplet overrides High/Low/ไฮโล
            odd_even = 'ตอง' # Triplet overrides Odd/Even

        results.append({
            'Die1': die1,
            'Die2': die2,
            'Die3': die3,
            'Total': total,
            'HighLow': high_low,
            'OddEven': odd_even,
            'Triplet': triplet
        })
    return pd.DataFrame(results)

def save_data(df: pd.DataFrame, filename: str = 'sicbo_data.csv', path: str = 'data/'):
    """
    Saves a DataFrame to a CSV file.

    Args:
        df (pd.DataFrame): The DataFrame to save.
        filename (str): The name of the CSV file.
        path (str): The directory to save the file in.
    """
    if not os.path.exists(path):
        os.makedirs(path)
    file_path = os.path.join(path, filename)
    df.to_csv(file_path, index=False)
    print(f"Data saved to {file_path}")

def load_data(filename: str = 'sicbo_data.csv', path: str = 'data/') -> pd.DataFrame:
    """
    Loads a DataFrame from a CSV file.

    Args:
        filename (str): The name of the CSV file.
        path (str): The directory to load the file from.

    Returns:
        pd.DataFrame: The loaded DataFrame.
    """
    file_path = os.path.join(path, filename)
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        print(f"Data loaded from {file_path}")
        return df
    else:
        print(f"File not found: {file_path}")
        return pd.DataFrame() # Return empty DataFrame if file not found

# Example usage (for testing this module directly)
if __name__ == "__main__":
    # Simulate and save
    sim_df = simulate_sicbo(100)
    save_data(sim_df)

    # Load and print
    loaded_df = load_data()
    print(loaded_df.head())
