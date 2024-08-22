#Code(2)
import pandas as pd
import json
import re
import string
from name_matching.name_matcher import NameMatcher
from cleanco import basename

# First, call the split code to generate a CSV file
def parse_jsonl_to_csv(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as jsonl_file:
        with open(output_path, 'w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Company Name', 'Search String']) # Write header

            for line in jsonl_file:
                data = json.loads(line)  # Convert each line of the JSON string into a dictionary
                company_name = data.get('companyName', '')
                required_search_strings = data.get('requiredSearchStrings', [])
                aliases = data.get('aliases', [])

                # Merge requiredSearchStrings and aliases and remove duplicates
                all_strings = list(set(required_search_strings + aliases))

                # Write a line for each string
                for string in all_strings:
                    csv_writer.writerow([company_name, string])

# Calling the split function
input_file_path = 'bd_companies_international.jsonl'
output_csv_path = 'output_companies.csv'
parse_jsonl_to_csv(input_file_path, output_csv_path)

# Read the generated CSV file
df_companies = pd.read_csv(output_csv_path)

# Next, use the name matching code to match
matcher = NameMatcher(number_of_matches=1, 
                      legal_suffixes=True, 
                      common_words=False, 
                      top_n=50, 
                      verbose=True)

matcher.set_distance_metrics(['ssk', 'discounted_levenshtein', 'fuzzy_wuzzy_partial_string'])

# Here we assume that the 'Company Name' column in df_companies is the master data we want to match
matcher.load_and_process_master_data(column='Company Name',
                                     df_matching_data=df_companies, 
                                     transform=True)

def preprocess(text):
    text = text.lower()
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(f'[{re.escape(string.punctuation)}]', '', text)
    text = basename(text)
    common_words = ['inc', 'ltd', 'corp', 'llc', 'co', 'company']
    for word in common_words:
        text = re.sub(r'\b{}\b'.format(re.escape(word)), '', text)
    text = ' '.join(text.split())
    return text

# User input
user_input = input("Enter the company you want to search: ")
processed_input = preprocess(user_input)

df_temp = pd.DataFrame([{'Search String': processed_input}])

matches = matcher.match_names(to_be_matched=df_temp, 
                              column_matching='Search String')

if not matches.empty:
    match_index = matches.iloc[0]['match_index']
    company_name = df_companies.iloc[match_index]['Company Name']
    print(f"Matched Company: {company_name}")
else:
    print("No Match Found")
