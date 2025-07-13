# src/analyzer.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def get_basic_statistics(df: pd.DataFrame) -> dict:
    """
    Calculates basic statistics from the Sic Bo DataFrame.

    Args:
        df (pd.DataFrame): The Sic Bo data DataFrame.

    Returns:
        dict: A dictionary containing various statistical insights.
    """
    if df.empty:
        return {"message": "No data to analyze."}

    stats = {}

    # High/Low/Triplet Distribution
    high_low_dist = df['HighLow'].value_counts(normalize=True) * 100
    stats['HighLow_Distribution'] = high_low_dist.to_dict()

    # Odd/Even Distribution
    odd_even_dist = df['OddEven'].value_counts(normalize=True) * 100
    stats['OddEven_Distribution'] = odd_even_dist.to_dict()

    # Total Score Distribution
    total_dist = df['Total'].value_counts(normalize=True).sort_index() * 100
    stats['Total_Distribution'] = total_dist.to_dict()

    # Individual Die Face Distribution
    die_faces = pd.concat([df['Die1'], df['Die2'], df['Die3']])
    die_face_dist = die_faces.value_counts(normalize=True).sort_index() * 100
    stats['DieFace_Distribution'] = die_face_dist.to_dict()
    
    # Triplet Occurrences
    triplet_count = df['Triplet'].sum()
    stats['Triplet_Count'] = int(triplet_count)
    stats['Triplet_Percentage'] = (triplet_count / len(df)) * 100 if len(df) > 0 else 0

    return stats

def plot_total_distribution(df: pd.DataFrame, title: str = 'การกระจายของแต้มรวม'):
    """
    Generates a bar plot for the distribution of total scores.

    Args:
        df (pd.DataFrame): The Sic Bo data DataFrame.
        title (str): Title of the plot.

    Returns:
        matplotlib.figure.Figure: The generated matplotlib Figure object.
    """
    if df.empty:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.countplot(x='Total', data=df, palette='viridis', ax=ax, order=sorted(df['Total'].unique()))
    ax.set_title(title)
    ax.set_xlabel('แต้มรวม')
    ax.set_ylabel('จำนวนครั้ง')
    plt.close(fig) # Prevent plot from showing immediately
    return fig

def plot_highlow_odd_distribution(df: pd.DataFrame, column: str, title: str):
    """
    Generates a pie chart or bar plot for High/Low or Odd/Even distribution.

    Args:
        df (pd.DataFrame): The Sic Bo data DataFrame.
        column (str): 'HighLow' or 'OddEven'.
        title (str): Title of the plot.

    Returns:
        matplotlib.figure.Figure: The generated matplotlib Figure object.
    """
    if df.empty:
        return None
    
    fig, ax = plt.subplots(figsize=(8, 8))
    # Filter out 'ตอง' for clearer High/Low and Odd/Even visualization
    plot_df = df[df[column] != 'ตอง'] 
    
    if plot_df[column].nunique() <= 3: # Use pie chart for simple categories
        plot_df[column].value_counts().plot.pie(autopct='%1.1f%%', startangle=90, ax=ax, cmap='coolwarm',
                                                 wedgeprops=dict(width=0.3))
        ax.set_ylabel('') # Hide y-label for pie chart
    else: # Use bar plot for more categories
        sns.countplot(x=column, data=plot_df, palette='coolwarm', ax=ax)
        ax.set_ylabel('จำนวนครั้ง')

    ax.set_title(title)
    plt.close(fig)
    return fig

def get_frequent_patterns(df: pd.DataFrame, pattern_length: int = 3, top_n: int = 5) -> dict:
    """
    Identifies and counts frequent sequential patterns of High/Low outcomes.

    Args:
        df (pd.DataFrame): The Sic Bo data DataFrame.
        pattern_length (int): Length of the pattern to search for (e.g., 3 for 'สูง-ต่ำ-สูง').
        top_n (int): Number of top patterns to return.

    Returns:
        dict: A dictionary of frequent patterns and their counts/percentages.
    """
    if df.empty or len(df) < pattern_length:
        return {"message": "Not enough data for pattern analysis."}

    # Exclude 'ตอง' from High/Low sequences for pattern analysis
    filtered_df = df[df['HighLow'].isin(['สูง', 'ต่ำ'])].copy()

    if len(filtered_df) < pattern_length:
        return {"message": "Not enough non-triplet data for pattern analysis."}

    patterns = {}
    for i in range(len(filtered_df) - pattern_length + 1):
        pattern = tuple(filtered_df['HighLow'].iloc[i : i + pattern_length].tolist())
        patterns[pattern] = patterns.get(pattern, 0) + 1
    
    sorted_patterns = sorted(patterns.items(), key=lambda item: item[1], reverse=True)
    
    result = {}
    for pattern, count in sorted_patterns[:top_n]:
        result["-".join(pattern)] = {
            "count": count,
            "percentage": (count / (len(filtered_df) - pattern_length + 1)) * 100
        }
    return result

# Example usage (for testing this module directly)
if __name__ == "__main__":
    # Assuming you have a DataFrame 'df_sicbo'
    # For testing, let's create a dummy one
    from src.data_generator import simulate_sicbo
    df_sicbo_test = simulate_sicbo(1000)

    stats = get_basic_statistics(df_sicbo_test)
    print("\n--- Basic Statistics ---")
    for k, v in stats.items():
        print(f"{k}: {v}")

    fig_total = plot_total_distribution(df_sicbo_test)
    if fig_total:
        fig_total.savefig('total_dist.png') # Save to check

    fig_highlow = plot_highlow_odd_distribution(df_sicbo_test, 'HighLow', 'การกระจาย สูง/ต่ำ')
    if fig_highlow:
        fig_highlow.savefig('highlow_dist.png')

    patterns = get_frequent_patterns(df_sicbo_test, pattern_length=3)
    print("\n--- Frequent High/Low Patterns (Length 3) ---")
    for p, details in patterns.items():
        print(f"Pattern: {p}, Count: {details['count']}, Percentage: {details['percentage']:.2f}%")
