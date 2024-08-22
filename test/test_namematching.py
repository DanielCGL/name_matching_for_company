import unittest
import pandas as pd
import re
import string
from name_matching.name_matcher import NameMatcher
from fuzzychinese import FuzzyChineseMatch
from rapidfuzz import process
from cleanco import basename

# 自定义测试结果类，用于记录测试结果并保存到 CSV 文件
class CustomTestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_results = []

    # 测试通过时调用
    def addSuccess(self, test):
        super().addSuccess(test)
        self.test_results.append((test.id(), 'PASS'))

    # 测试失败时调用
    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.test_results.append((test.id(), 'FAIL', self._exc_info_to_string(err, test)))

    # 测试错误时调用
    def addError(self, test, err):
        super().addError(test, err)
        self.test_results.append((test.id(), 'ERROR', self._exc_info_to_string(err, test)))

    # 打印错误信息
    def printErrors(self):
        super().printErrors()

    # 转换异常信息为字符串
    def _exc_info_to_string(self, err, test):
        return self._format_exc_info(err, test)

    # 测试运行结束时调用
    def stopTestRun(self):
        super().stopTestRun()
        # 将测试结果保存到 CSV 文件
        pd.DataFrame(self.test_results, columns=['Test ID', 'Result', 'Details']).to_csv('test_results.csv', index=False)

# 测试类，用于测试公司名称匹配功能
class TestNameMatching(unittest.TestCase):
    # 定义中文字符的 Unicode 范围
    CJK_CHARACTERS = r'\u1100-\u11ff\u2e80-\u2fff\u3040-\u31ff\u3400-\u9fff\ua960-\ua97f\uac00-\ud7ff\uf900-\ufaff'

    def setUp(self):
        # 初始化名称匹配器
        self.matcher = NameMatcher(
            number_of_matches=1,
            legal_suffixes=True,
            common_words=False,
            top_n=50,
            verbose=True
        )
        # 读取英文和中文搜索字符串数据
        df_english = pd.read_csv('english_search_strings.csv')
        df_chinese = pd.read_csv('chinese_search_strings.csv')
        self.company_names = df_chinese['Company Name']
        # 初始化 FuzzyChineseMatch 对象
        self.fcm = FuzzyChineseMatch(ngram_range=(3, 3), analyzer='stroke')
        self.fcm.fit(self.company_names)
        # 加载并处理主数据
        self.matcher.load_and_process_master_data(column='Search String', df_matching_data=df_english, transform=True)

    # 预处理文本函数
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

    # 测试名称匹配
    def test_name_matching(self):
        # 读取过滤后的公司名称数据
        filtered_data = pd.read_csv('filtered_company_names.csv')
        for index, row in filtered_data.iterrows():
            user_input = row['company name']
            expected_output = row['expected company name']
            with self.subTest(f"Test {index + 1:03d} - {user_input}"):
                # 执行名称匹配
                matched_company_name = self.match_name(user_input)
                # 断言匹配结果是否符合预期
                self.assertEqual(matched_company_name, expected_output, f"Failed matching: {user_input} -> Expected: {expected_output}, Got: {matched_company_name}")

    # 名称匹配函数
    def match_name(self, user_input):
        if re.search(self.CJK_CHARACTERS, user_input):
            # 中文匹配逻辑
            user_input_series = pd.Series([user_input])
            top_matches = self.fcm.transform(user_input_series, n=1)
            matched_index = self.fcm.get_index()[0][0]
            return self.company_names.iloc[matched_index]
        else:
            # 英文匹配逻辑
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

# 程序入口，运行测试
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestNameMatching)
    runner = unittest.TextTestRunner(stream=sys.stdout, resultclass=CustomTestResult, verbosity=2)
    runner.run(suite)
