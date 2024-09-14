#This is a unittest code for testing multiple samples
class TestCompanyMatcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the CompanyMatcher and load the data once for all tests."""
        cls.matcher = CompanyMatcher('bd_companies_international.jsonl')

        # Load Company Data
        cls.companies = cls.matcher.load_company_data()

        # Prepare matching data
        cls.matcher.matching_data = cls.matcher.prepare_matching_data(cls.companies)

        # Load and process the master data for matching
        cls.matcher.prepare_data_for_matching(cls.matcher.matching_data)  # 加载并处理主数据

        # Print matching_data sample to check if the alias is loaded correctly
        print("Sample of matching data in setUpClass:")
        print(cls.matcher.matching_data[['name', 'companyName', 'alias_name']].head(10))

    def test_company_name_matching(self):
        """Test the company name matching with input from the CSV file."""
        test_data = pd.read_csv('filtered_company_names.csv')

        with open('company_name_matching_results.csv', 'w', newline='', encoding='utf-8') as output_file:
            writer = csv.writer(output_file)
            writer.writerow(['company name', 'expected company name', 'output', 'true/false'])

            for index, row in test_data.iterrows():
                input_name = row['company name']
                expected_name = row['expected company name']

                start_time = time.time()

                # Match the user input with the company name or alias
                output_name = self.matcher.match_user_input(input_name, expected_name)  # 传入 expected_name 参数

                end_time = time.time()
                elapsed_time = end_time - start_time

                # Ensure expected_name and output_name are strings to prevent AttributeError
                if pd.isna(expected_name):
                    expected_name = ''
                if pd.isna(output_name):
                    output_name = ''

                # Both output and expected are empty, set result to True
                if output_name == '' and expected_name == '':
                    result = True
                else:
                    result = output_name.lower() == expected_name.lower()

                # Output CSV
                writer.writerow([input_name, expected_name, output_name, result])


if __name__ == '__main__':
    unittest.main()
