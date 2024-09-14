#Calculate score of precision, accuracy, recall, and F1-score, it will also generate a graph of the 4 score lines.
import pandas as pd
import matplotlib.pyplot as plt

# Define the starting and ending thresholds (can be adjusted as needed)
start_threshold = 65  # Starting threshold
end_threshold = 95    # Ending threshold

# Initialize an empty list to store results for each file
results = []

# Loop through the specified range of CSV files
for i in range(start_threshold, end_threshold + 1):  # Range is from start to end
    # Construct the filename
    file_name = f'company_name_matching_results_threshold_{i}.csv'

    # Load the CSV file
    try:
        data = pd.read_csv(file_name)
    except FileNotFoundError:
        print(f"File {file_name} not found. Skipping...")
        continue

    # Calculate TP (True Positive), FP (False Positive), FN (False Negative), TN (True Negative)
    tp = data[(data['true/false'] == True) & (data['output'].notna())].shape[0]
    fp = data[(data['true/false'] == False) & (data['output'].notna())].shape[0]
    fn = data[(data['true/false'] == False) & (data['output'].isna())].shape[0]
    tn = data[(data['true/false'] == True) & (data['output'].isna())].shape[0]

    # Calculate Precision, Accuracy, Recall, and F1-score
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # Store the results in a dictionary
    results.append({
        'threshold': i,
        'TP': tp,
        'FP': fp,
        'FN': fn,
        'TN': tn,
        'Precision': precision,
        'Accuracy': accuracy,
        'Recall': recall,
        'F1-score': f1_score
    })

# Convert the results into a DataFrame and save them to a CSV file
results_df = pd.DataFrame(results)
results_df.to_csv('calculate_score.csv', index=False)

# Plot Precision, Recall, F1-score, and Accuracy curves
plt.figure(figsize=(10, 6))
plt.plot(results_df['threshold'], results_df['Precision'], label='Precision', marker='o')
plt.plot(results_df['threshold'], results_df['Recall'], label='Recall', marker='o')
plt.plot(results_df['threshold'], results_df['F1-score'], label='F1-score', marker='o')
plt.plot(results_df['threshold'], results_df['Accuracy'], label='Accuracy', marker='o')

# Set x-axis ticks to show every 2 steps
plt.xticks(ticks=range(0, results_df['threshold'].max() + 1, 2))

# Set chart title and labels
plt.xlabel('Threshold')
plt.ylabel('Score')
plt.title('Performance Metrics vs Threshold')
plt.legend()
plt.grid(True)

# Display the plot
plt.show()
