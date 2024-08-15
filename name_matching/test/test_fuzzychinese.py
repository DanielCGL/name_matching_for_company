#!pip install fuzzychinese
import pandas as pd
from fuzzychinese import FuzzyChineseMatch

def find_company_name(user_input, csv_file='chinese_search_strings.csv'):
    # Load your CSV file
    df = pd.read_csv(csv_file)

    # Extract the 'search string' and 'company name' columns
    search_strings = df['Search String']
    company_names = df['Company Name']

    # Initialize FuzzyChineseMatch
    fcm = FuzzyChineseMatch(ngram_range=(3, 3), analyzer='stroke')
    fcm.fit(search_strings)

    # Find the top matches for the user input
    user_input_series = pd.Series([user_input])
    top_matches = fcm.transform(user_input_series, n=1)  # Get the top 1 match

    # Retrieve the matching company name
    matched_index = fcm.get_index()[0][0]  # Index of the top match
    matched_company_name = company_names.iloc[matched_index]

    return matched_company_name

# User input
user_input = input("Please enter something: ")  # Replace with the actual user input

# Get the matched company name
matched_company_name = find_company_name(user_input)

# Output the result
print(f"User Input: {user_input}")
print(f"Matched Company Name: {matched_company_name}")
