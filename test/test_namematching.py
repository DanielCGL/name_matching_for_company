#This is a unittest code for testing multiple samples with one threshold, modify threshold in the usage.py file, match_score under match_user_input. 
import unittest
import pandas as pd
import re
import string
from name_matching.name_matcher import NameMatcher
from fuzzychinese import FuzzyChineseMatch
from rapidfuzz import process
from cleanco import basename

# Custom test result class to record test results and save them to a CSV file.
class CustomTestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_results = []

    # Called when a test passes.
    def addSuccess(self, test):
        super().addSuccess(test)
        self.test_results.append((test.id(), 'PASS'))

    # Called when a test fails.
    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.test_results.append((test.id(), 'FAIL', self._exc_info_to_string(err, test)))

    # Called when a test raises an error.
    def addError(self, test, err):
        super().addError(test, err)
        self.test_results.append((test.id(), 'ERROR', self._exc_info_to_string(err, test)))

    # Print error information.
    def printErrors(self):
        super().printErrors()

    # Convert exception information to a string.
    def _exc_info_to_string(self, err, test):
        return self._format_exc_info(err, test)

    # Called when the test run is stopped.
    def stopTestRun(self):
        super().stopTestRun()
        # Save test results to a CSV file.
        pd.DataFrame(self.test_results, columns=['Test ID', 'Result', 'Details']).to_csv('test_results.csv', index=False)

# Test class for testing company name matching functionality.
class TestNameMatching(unittest.TestCase):
    # Define the Unicode range for Chinese characters.
    CJK_CHARACTERS = r'\u1100-\u11ff\u2e80-\u2fff\u3040-\u31ff\u3400-\u9fff\ua960-\ua97f\uac00-\ud7ff\uf900-\ufaff'

    def setUp(self):
        # Initialize the name matcher with specific parameters.
        self.matcher = NameMatcher(
            number_of_matches=1,
            legal_suffixes=True,
            common_words=False,
            top_n=50,
            verbose=True
        )
        # Read English and Chinese search string data into DataFrames.
        df_english = pd.read_csv('english_search_strings.csv')
        df_chinese = pd.read_csv('chinese_search_strings.csv')
        self.company_names = df_chinese['Company Name']
        # Initialize the FuzzyChineseMatch object with specific parameters.
        self.fcm = FuzzyChineseMatch(ngram_range=(3, 3), analyzer='stroke')
        self.fcm.fit(self.company_names)
        # Load and process the master data for matching.
        self.matcher.load_and_process_master_data(column='Search String', df_matching_data=df_english, transform=True)

    # Preprocess the text for matching.
    def preprocess(self, text):
        text = text.lower()
        text = text.encode('ascii', 'ignore').decode('ascii')
        text = re.sub(f'[{re.escape(string.punctuation)}]', '', text)
        text = basename(text)
        common_words = ['inc', 'ltd', 'corp', 'llc', 'co', 'company']
        for word in common_words:
            text = re.sub(r'\b{}\b'.format(re.escape(word)), '', text)
        text = ' '.join(text.split())
        return text

    # Test the name matching process.
    def test_name_matching(self):
        # Read filtered company name data into a DataFrame.
        filtered_data = pd.read_csv('filtered_company_names.csv')
        for index, row in filtered_data.iterrows():
            user_input = row['company name']
            expected_output = row['expected company name']
            with self.subTest(f"Test {index + 1:03d} - {user_input}"):
                # Perform the name matching.
                matched_company_name = self.match_name(user_input)
                # Assert that the matched result is as expected.
                self.assertEqual(matched_company_name, expected_output, f"Failed matching: {user_input} -> Expected: {expected_output}, Got: {matched_company_name}")

    # Function to match names based on the input language.
    def match_name(self, user_input):
        if re.search(self.CJK_CHARACTERS, user_input):
            # Logic for matching Chinese characters using FuzzyChineseMatch.
            user_input_series = pd.Series([user_input])
            top_matches = self.fcm.transform(user_input_series, n=1)
            matched_index = self.fcm.get_index()[0][0]
            return self.company_names.iloc[matched_index]
        else:
            # Logic for matching English characters using NameMatcher and rapidfuzz.
            processed_input = self.preprocess(user_input)
            df_temp = pd.DataFrame([{'Search String': processed_input}])
            matches = self.matcher.match_names(to_be_matched=df_temp, column_matching='Search String')
            input_string = '\n'.join(matches['match_name'].dropna().astype(str))
            df = pd.read_csv('english_search_strings.csv')
            best_match = process.extractOne(input_string, df['Search String'])
            if best_match:
                matched_row = df[df['Search String'] == best_match[0]]
                return matched_row['Company Name'].values[0]
            return None

# Main program entry point to run the tests.
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestNameMatching)
    runner = unittest.TextTestRunner(stream=sys.stdout, resultclass=CustomTestResult, verbosity=2)
    runner.run(suite)
