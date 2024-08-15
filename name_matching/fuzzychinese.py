#fuzzychinese
"""
This is a part of the code where the search string and the user input contains chinese characters. 
When chinese characters detected, fuzzychinese will start to matching chinese search string.
This requires a pip for the fuzzychinese package
"""
!pip install fuzzychinese
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
