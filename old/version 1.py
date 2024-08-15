#Version 1
# This version has a problem, the aliases cannot been searched.
#!pip install cleanco
import pandas as pd
import json
import re
import string
from name_matching.name_matcher import NameMatcher
from cleanco import basename


# read data
with open('bd_companies_international.jsonl', 'r', encoding='utf-8') as file:
    data = [json.loads(line) for line in file]

df_companies_a = pd.DataFrame([{'Company name': item['companyName']} for item in data])

df_companies_b = pd.DataFrame([{'name': item['requiredSearchStrings'][0] if 'requiredSearchStrings' in item and item['requiredSearchStrings'] else ''} for item in data])

df_aliases = pd.DataFrame([{'aliases': item['aliases'][0] if 'aliases' in item and item['aliases'] else ''} for item in data])

matcher = NameMatcher(number_of_matches=1, 
                      legal_suffixes=True, 
                      common_words=False, 
                      top_n=50, 
                      verbose=True)

matcher.set_distance_metrics(['ssk', 'discounted_levenshtein', 'fuzzy_wuzzy_partial_string'])

matcher.load_and_process_master_data(column='Company name',
                                     df_matching_data=df_companies_a, 
                                     transform=True)

def preprocess(text):
    # Remove all uppercase letters and convert them to lowercase
    text = text.lower()
    # Replace non-ASCII characters
    text = text.encode('ascii', 'ignore').decode('ascii')
    # Remove punctuation
    text = re.sub(f'[{re.escape(string.punctuation)}]', '', text)
    # Use cleanco to remove legitimate business suffixes
    text = basename(text)
    # Remove the most common words (such as "inc", "ltd", etc.)
    common_words = ['inc', 'ltd', 'corp', 'llc', 'co', 'company']
    for word in common_words:
        text = re.sub(r'\b{}\b'.format(re.escape(word)), '', text)
    # Remove extra spaces
    text = ' '.join(text.split())
    return text

user_input = input("Please enter your company name: ")
processed_input = preprocess(user_input)

df_temp = pd.DataFrame([{'name': processed_input}])

matches = matcher.match_names(to_be_matched=df_temp, 
                              column_matching='name')

if not matches.empty:
    match_index = matches.iloc[0]['match_index']
    company_name = df_companies_a.iloc[match_index]['Company name']
    print(f"Matched Company Name: {company_name}")
else:
    print("No Matches Found")
