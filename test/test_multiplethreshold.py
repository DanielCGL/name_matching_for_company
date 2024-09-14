"""This is a unittest code for testing multiple samples with multiple thresholds. 
   This requires to do some action before running this code, modify these things below in the usage.py:
   1.change def(match_user_input) to def match_user_input(self, user_input: str, expected_name: str, threshold: int = 70) -> str:
   2.change match_score >= 70 to match_score >= threshold in match_user_input
"""
import unittest
import pandas as pd
import csv
import time
from name_matching_for_company import CompanyMatcher
class TestCompanyMatcher(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up the CompanyMatcher and load the data once for all tests."""
        cls.matcher = CompanyMatcher('bd_companies_international.jsonl')
        cls.companies = cls.matcher.load_company_data()
        cls.matcher.matching_data = cls.matcher.prepare_matching_data(cls.companies)
        cls.matcher.prepare_data_for_matching(cls.matcher.matching_data)

    def test_company_name_matching_dynamic_threshold(self):
        """Test the company name matching with dynamic threshold."""
        test_data = pd.read_csv('filtered_company_names.csv')

        # Loop from match_score >= 1 to match_score >= 100
        for threshold in range(65, 96):
            with self.subTest(threshold=threshold):  # Use unittest subTest for each threshold
                # Output CSV file for this specific threshold
                output_filename = f'company_name_matching_results_threshold_{threshold}.csv'

                # Prepare output file
                with open(output_filename, 'w', newline='', encoding='utf-8') as output_file:
                    writer = csv.writer(output_file)
                    writer.writerow(['company name', 'expected company name', 'output', 'true/false', 'time (seconds)'])

                    # Iterate over test data
                    for index, row in test_data.iterrows():
                        input_name = row['company name']
                        expected_name = row['expected company name']

                        start_time = time.time()

                        # Call match_user_input with the dynamic threshold
                        output_name = self.matcher.match_user_input(input_name, expected_name, threshold=threshold)

                        end_time = time.time()
                        elapsed_time = end_time - start_time

                        # Ensure expected_name and output_name are strings
                        expected_name = '' if pd.isna(expected_name) else expected_name
                        output_name = '' if pd.isna(output_name) else output_name

                        # Determine if the output matches the expected name
                        result = output_name.lower() == expected_name.lower()

                        # Write the result to the CSV file
                        writer.writerow([input_name, expected_name, output_name, result, elapsed_time])

if __name__ == '__main__':
    unittest.main()

