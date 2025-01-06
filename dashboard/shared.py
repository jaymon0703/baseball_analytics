from pathlib import Path

import pandas as pd

app_dir = Path(__file__).parent
df_pitchers_2024 = pd.read_csv(app_dir / "2024_pitchers.csv", header=None)
ls_pitchers_2024 = df_pitchers_2024[0].tolist()

def create_count_matrix(df):
    """
    Converts a list of numbers (1-9) into a 3x3 count matrix.

    Args:
        numbers: A list of integers.

    Returns:
        A 3x3 matrix (list of lists) representing the counts of each number.
    """

    matrix = [[0, 0, 0],
              [0, 0, 0],
              [0, 0, 0]]

    for num in df["zone"]:
        if 1 <= num <= 9:  # Only consider numbers from 1 to 9
            row = int((num) // 3)  # Integer division to get the row index
            col = int((num - 1) % 3 + 1)  # Modulo to get the column index
            matrix[row-1][col-1] += 1

    return matrix
