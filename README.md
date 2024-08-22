# Please Note: This package is in progress!

# Name matching for company
This is a forked repository from:
[![name_matching](https://github.com/DeNederlandscheBank/name_matching/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/DeNederlandscheBank/name_matching/actions/workflows/python-app.yml)

This is a package that use to match company names in your database. You should be providing:

        - a database that has all company names, including its aliases if possible.
        - a search string that use to match the user input
        
This package only supports any alphabetical language and Chinese, please make sure to not contain any other language in the database.
When the package detect the user input is in Chinese, the program will automatically use fuzzychinese to match the name. 
When the package detect the user input is in English, the program will automatically use name_matching to match the name. 


## Requirements

The following package needs to install before running this package.

[fuzzychinese](https://github.com/znwang25/fuzzychinese)
```bash
pip install fuzzychinese
```

[rapidfuzz](https://github.com/rapidfuzz/RapidFuzz)
```bash
pip install rapidfuzz
```

[abydos](https://github.com/chrislit/abydos)
```bash
pip install rapidfuzz
```


## Installation for this package
```bash
pip install git+https://github.com/DanielCGL/name_matching_for_company.git
```

## Pre-Run

Before running the usage code, user should have a jsonl file that contains the following information:

        - requiredSearchStrings for the string matches with the user_input and,
        - the correspond companyName for output
        
For Example:
```bash
{"requiredSearchStrings":["apples","apple","苹果","itunes"],"aliases":["iTunes","Apple's","Apple","苹果公司"],"companyName":"Apple Inc."}
```


## Usage
```python
#!pip install fuzzychinese
#!pip install git+https://github.com/DanielCGL/name_matching_for_company.git
#!pip install rapidfuzz
import pandas as pd
import json
import re
import string
from name_matching.name_matcher import NameMatcher
from cleanco import basename
from fuzzychinese import FuzzyChineseMatch
from rapidfuzz import process

# Regular expression for recognizing CJK characters
CJK_CHARACTERS = r'\u1100-\u11ff\u2e80-\u2fff\u3040-\u31ff\u3400-\u9fff\ua960-\ua97f\uac00-\ud7ff\uf900-\ufaff'
CJK_OR_NUMERIC_REGEX = re.compile(rf"(?P<cjk>[{CJK_CHARACTERS}]+)|(?P<numeric>((?<=^\D)|(?<=[^\W0-9_]|\s))(?<!\b[a-zA-Z])(\d+([\W_]{{0,5}}\d+){{0,5}})(?=($|[^\W0-9_]|\s)))")
# Segment English text
"""Matches any character that is not an alphanumeric character,
underscore, plus sign, asterisk, forward slash, single quote, pound sign, or dash.
In the context of text segmentation, it has the effect of splitting the text into words,
ignoring the special characters specified above while retaining those special characters as delimiters."""
ENGLISH_SPLITTER_REGEX = re.compile(r"[^\w&_+*\\/'#\-]+")


def split_english_number_cjk(text, separate_return=True, split_same_language=False):
    """A Function to split a given text into English/numeric words and CJK (Chinese, Japanese, Korean) characters.
    It uses regular expressions to identify and separate these different types of characters."""
    # Initialize lists to hold English/numeric words and CJK words
    en_number_words = []
    cjk_words = []
    
    # Set the start index to the beginning of the text and the end index to the length of the text
    start, end = 0, len(text)
    
    # Loop through the text while there are still characters to process and the regex finds matches
    while start < end and (r_ := CJK_OR_NUMERIC_REGEX.search(text, pos=start)):
        # Check if there is an English/numeric word before the current match and add it to the list
        if word := text[start:r_.start()].strip():
            if split_same_language:
                # Extend the list with individual words
                en_number_words.extend(
                    [stripped_word for word_ in ENGLISH_SPLITTER_REGEX.split(word) if (stripped_word := word_.strip())])
            else:
                # Append the whole word
                en_number_words.append(word)
        
        # Check if there is a CJK character match and add it to the respective list
        if cjk_word := r_.groupdict().get("cjk"):
            if split_same_language:
                # Add each character to the list
                (cjk_words if separate_return else en_number_words).extend(list(cjk_word))
            else:
                # Add the whole CJK word
                (cjk_words if separate_return else en_number_words).append(cjk_word)
        else:
            # Handle it similarly when there's a numeric match.
            numeric_word = r_.groupdict().get("numeric")
            if split_same_language:
                en_number_words.extend([stripped_word for word_ in ENGLISH_SPLITTER_REGEX.split(numeric_word) if (stripped_word := word_.strip())])
            else:
                en_number_words.append(numeric_word)
        
        # Update the start index to the end of the current match for the next iteration.
        start = r_.end()

    # Check if there is any remaining text to process.
    if end > start and (text := text[start:].strip()):
        if split_same_language:
            # Extend the list with individual words if splitting within the same language.
            en_number_words.extend([word_ for word in ENGLISH_SPLITTER_REGEX.split(text) if (word_ := word.strip())])
        else:
            # Append the remaining text as a whole word if not splitting.
            en_number_words.append(text)
    
    # Return a tuple of both lists if separate_return is True, otherwise return only the list of English/numeric words.
    return (en_number_words, cjk_words) if separate_return else en_number_words


def parse_and_separate_jsonl(input_path):
    """
    Parses a JSON Lines (.jsonl) file and separates the data into English and Chinese lists.

    Parameters:
    - input_path (str): The file path to the JSON Lines file to be parsed.

    Returns:
    - df_english (pd.DataFrame): A DataFrame containing English search strings associated with company names.
    - df_chinese (pd.DataFrame): A DataFrame containing Chinese search strings associated with company names.
    """

    # Initialize empty lists to hold English and Chinese company names and search strings
    english_list = []
    chinese_list = []

    # Open the JSON Lines file for reading with UTF-8 encoding
    with open(input_path, 'r', encoding='utf-8') as jsonl_file:
        # Iterate over each line in the file.
        for line in jsonl_file:
            # Parse the JSON data from the current line
            data = json.loads(line)
            
            # Extract the company name and default to an empty string if not present
            company_name = data.get('companyName', '')
            
            # Extract the required search strings and aliases, and combine them into a set to remove duplicates
            required_search_strings = data.get('requiredSearchStrings', [])
            aliases = data.get('aliases', [])
            all_strings = list(set(required_search_strings + aliases))

            # Process each unique string from the combined list
            for string in all_strings:
                # Separate the string into English/numeric and CJK parts
                en_strings, cjk_strings = split_english_number_cjk(string, separate_return=True)
                
                # Append the English/numeric parts to the English list with associated company name
                for en_str in en_strings:
                    english_list.append({'Company Name': company_name, 'Search String': en_str})
                
                # Append the CJK parts to the Chinese list with associated company name
                for cjk_str in cjk_strings:
                    chinese_list.append({'Company Name': company_name, 'Search String': cjk_str})

    # Convert the English list of dictionaries to a DataFrame
    df_english = pd.DataFrame(english_list)
    
    # Convert the Chinese list of dictionaries to a DataFrame
    df_chinese = pd.DataFrame(chinese_list)

    # Return the two DataFrames containing the separated English and Chinese data
    return df_english, df_chinese

# Parse JSONL and separate English and Chinese strings
input_file_path = 'xxx.jsonl'#input your jsonl file, the database file
df_english, df_chinese = parse_and_separate_jsonl(input_file_path)

# Save Chinese and English strings to CSV
df_chinese.to_csv('chinese_search_strings.csv', index=False, encoding='utf-8-sig')
df_english.to_csv('english_search_strings.csv', index=False, encoding='utf-8-sig')

# Initialize name matcher
matcher = NameMatcher(number_of_matches=1, 
                      legal_suffixes=True, 
                      common_words=False, 
                      top_n=50, 
                      verbose=True)

# Load and process split English string data
df_english = pd.read_csv('english_search_strings.csv')
matcher.load_and_process_master_data(column='Search String', df_matching_data=df_english, transform=True)

# Load and process split Chinese string data
df_chinese = pd.read_csv('chinese_search_strings.csv')
search_strings = df_chinese['Search String']
company_names = df_chinese['Company Name']
fcm = FuzzyChineseMatch(ngram_range=(3, 3), analyzer='stroke')
fcm.fit(search_strings)

def preprocess(text):
    """
    Preprocesses the given text by performing the following operations:
    1. Converts the text to lowercase.
    2. Removes non-ASCII characters.
    3. Removes punctuation.
    4. Removes common words that may not be necessary for processing.
    5. Trims extra spaces and returns a clean, single-line string.

    Parameters:
    - text (str): The input text to preprocess.

    Returns:
    - str: The preprocessed text.
    """

    # Convert the text to lowercase
    text = text.lower()

    # Encode to ASCII and ignore non-ASCII characters, then decode back to ASCII
    # This removes any non-ASCII characters from the text
    text = text.encode('ascii', 'ignore').decode('ascii')

    # Remove punctuation using a regular expression that matches all punctuation characters and replaces them with an empty string
    text = re.sub(f'[{re.escape(string.punctuation)}]', '', text)

    # Apply the 'basename' function to the text to remove certain prefixes or suffixes
    text = basename(text)

    # Define a list of common words to remove from the text
    common_words = ['inc', 'ltd', 'corp', 'llc', 'co', 'company']

    # Iterate over the list of common words and remove them from the text using a regular expression that matches whole words only
    for word in common_words:
        text = re.sub(r'\b{}\b'.format(re.escape(word)), '', text)

    # Split the text into words and rejoin them with a single space to ensure there are no extra spaces in the final output
    text = ' '.join(text.split())

    # Return the preprocessed text
    return text

def find_company_name(user_input, csv_file='chinese_search_strings.csv'):
    """
    Uses the FuzzyChinese library to match a Chinese user input to a company name from a CSV file.

    The function performs the following steps:
    1. Loads the CSV file containing search strings and corresponding company names.
    2. Initializes the FuzzyChineseMatch object with specified n-gram range and analyzer.
    3. Fits the FuzzyChineseMatch object with the search strings from the CSV.
    4. Transforms the user input into a pandas Series and finds the top match using the FuzzyChineseMatch.
    5. Retrieves and returns the matched company name from the company names DataFrame.

    Parameters:
    - user_input (str): The Chinese input string from the user to be matched against company names.
    - csv_file (str, optional): The path to the CSV file containing 'Search String' and 'Company Name' columns. Defaults to 'chinese_search_strings.csv'.

    Returns:
    - str: The matched company name for the user input.
    """
    # Load the CSV file
    df = pd.read_csv(csv_file)

    # Extract the 'search string' and 'company name' columns
    search_strings = df['Search String']
    company_names = df['Company Name']

    # Initialize FuzzyChineseMatch
    fcm = FuzzyChineseMatch(ngram_range=(3, 3), analyzer='stroke')
    fcm.fit(search_strings)

    # Find the top matches for the user input
    user_input_series = pd.Series([user_input])
    # Get the top 1 match
    top_matches = fcm.transform(user_input_series, n=1)  

    # Retrieve the matching company name
    matched_index = fcm.get_index()[0][0]  # Index of the top match
    matched_company_name = company_names.iloc[matched_index]
    return matched_company_name

def match_company_name(input_string, df):
    """
    Matches the input string to the closest 'Search String' in the given DataFrame and returns the corresponding 'Company Name'.

    The function performs the following steps:
    1. Reads a CSV file 'english_search_strings.csv' into a DataFrame. Note that the parameter 'df' is not used.
    2. Uses the rapidfuzz process to find the single best match for the input string within the 'Search String' column of the DataFrame.
    3. If a match is found, retrieves the corresponding 'Company Name' from the matched row.
    4. Returns the matched 'Company Name' or None if no match is found.

    Parameters:
    - input_string (str): The string to be matched against the 'Search String' column.
    - df (pandas.DataFrame): The DataFrame containing 'Search String' and 'Company Name' columns. This parameter is redundant as the function reads the CSV file directly.

    Returns:
    - str or None: The matched 'Company Name' if a match is found, otherwise None.
    """

    # Read the CSV file into a DataFrame
    df = pd.read_csv('english_search_strings.csv')
    
    # Use rapidfuzz's process to find the closest match for the input string in the 'Search String' column
    best_match = process.extractOne(input_string, df['Search String'])
    
    # Retrieve the corresponding 'Company Name' when match found
    if best_match:
        matched_row = df[df['Search String'] == best_match[0]]
        return matched_row['Company Name'].values[0]
    else:
        # Return None when matches not found
        return None

user_input = input("请输入匹配的名称: ") # Your input

# Check weather input contains any Chinese characters using a regular expression search
if re.search(f'[{CJK_CHARACTERS}]', user_input):
    # If the input contains Chinese characters, use the find_company_name function which utilizes fuzzychinese to match the input and find the corresponding company name
    matched_company_name = find_company_name(user_input)
    print(f"匹配到的公司名称是: {matched_company_name}")

else:
    # using the preprocess function
    processed_input = preprocess(user_input)

    # Create a temporary DataFrame with the preprocessed input
    df_temp = pd.DataFrame([{'Search String': processed_input}])

    # Use a NameMatcher instance to match the preprocessed input against the 'Search String' column
    matches = matcher.match_names(to_be_matched=df_temp, column_matching='Search String')

    # Print the content of the 'Matches' DataFrame for debugging purposes
    print("Matches DataFrame content:", matches.head())

    # Join the matched 'Search String' values into a single string and use the match_company_name function to find the associated 'Company Name'
    input_string = ('\n'.join(matches['match_name'].dropna().astype(str)))
    company_name = match_company_name(input_string, df)

    # Check if a company name was matched and print the result
    if company_name:
        print(f"匹配到的公司名称是: {company_name}")
    else:
        print("没有匹配到相应的公司名称")
```

Output:

user_input: Apple

output: Apple.lnc.*

user_input: 苹果

output: Apple.lnc.*

* = output search by my database

Not only it will output you the matching company, it will also output you two csv files, these two files are your database separated with chinese search string and english search string data.


## Contributing
All contributions are welcome. For more substantial changes, please open an issue first to discuss what you would like to change.


## License
The code is licensed under the MIT/X license an extended version of the licence: [MIT](https://choosealicense.com/licenses/mit/)


## Thanks
Thanks to the work of implementing name matching algorithms done in the [Abydos package](https://github.com/chrislit/abydos),the base of this program [name-matching](https://github.com/DeNederlandscheBank/name_matching), contributors of [rapidfuzz](https://github.com/rapidfuzz/RapidFuzz), and contributors of fuzzychinese[fuzzychinese](https://github.com/znwang25/fuzzychinese). These form the basis algorithms used in this package.
