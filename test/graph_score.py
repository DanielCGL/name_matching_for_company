#Graph score for Precision vs Recall, need to run calculate_score.py and output a csv file before running this.
import pandas as pd
import matplotlib.pyplot as plt

# Upload CSV File
data = pd.read_csv('calculate_score9.csv')

# Plotting Precision vs Recall
plt.figure(figsize=(8, 6))
plt.plot(data['Recall'], data['Precision'], marker='o')

# Add axis labels and titles
plt.xlabel('Recall')
plt.ylabel('Precision')
plt.title('Precision vs Recall')

# Show grid
plt.grid(True)

# Show graph
plt.show()
