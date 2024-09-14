# Name matching for company
This is a forked repository from:
[![name_matching](https://github.com/DeNederlandscheBank/name_matching/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/DeNederlandscheBank/name_matching/actions/workflows/python-app.yml)


## Overview
This code is a Company Name Normalization and Matching System that handles the normalization, tokenization, and matching of company names, both in English and Chinese, using a combination of regular expressions, tokenization (via Jieba for Chinese), and matching algorithms. 

The goal of this code is to match user-provided company names against a predefined set of company names and their aliases. This is particularly useful for standardizing company names that may appear in various forms, languages, or with different symbols and suffixes. 

The system aims to normalize and match company names in both English and Chinese, ensuring that variations in name formatting, spelling, and symbols do not hinder matching. This is especially useful for large-scale datasets where company names appear in multiple forms across different documents or regions.

This is a package that use to match company names in your database. You should be providing:

        - a database that has all company names, including its aliases if possible.
        - a search string that use to match the user input


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
See [usage.py](https://github.com/DanielCGL/name_matching_for_company/blob/main/usage.py)

Explanation: Suppose a user inputs the company name "Google LLC," but the system has the company listed as "Google Inc." The system would:

Remove the suffix "LLC."
Tokenize the name if needed.
Compare the cleaned name against its list of known companies and aliases (which includes "Google Inc.") and return the matching company name, "Google Inc."


## Workflow
1.Normalization:
The user-provided company name is cleaned by removing irrelevant symbols, normalizing circumflexes (e.g., é → e), and removing common suffixes and words.

2.Tokenization:
If the company name contains Chinese characters, it is tokenized using Jieba. For mixed English-Chinese strings, the English and Chinese parts are processed separately.

3.Matching:
The cleaned and tokenized company name is matched against a preloaded list of company names and aliases. The NameMatcher algorithm determines the closest match based on a threshold score.

4.Result:
If the company name matches one of the known companies (or its aliases), the system returns the matched company name; otherwise, it returns an empty string.

## Performance
![Figure_2 for precision vs recall](https://github.com/user-attachments/assets/216cdf11-1c34-43b2-a2aa-8f02255cff29)


## Contributing
All contributions are welcome. For more substantial changes, please open an issue first to discuss what you would like to change.


## License
The code is licensed under the MIT/X license an extended version of the licence: [MIT](https://choosealicense.com/licenses/mit/)


## Thanks
Thanks to the work of implementing name matching algorithms done in the [Abydos package](https://github.com/chrislit/abydos),the base of this program [name-matching](https://github.com/DeNederlandscheBank/name_matching), the contributor of jieba[jieba](https://github.com/fxsjy/jieba). These form the basis algorithms used in this package and usage.
