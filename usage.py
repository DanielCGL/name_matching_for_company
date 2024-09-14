import re
import pandas as pd
import json
import jieba
from name_matching.name_matcher import NameMatcher

# A regular expression to match and replace certain symbols with spaces, including slashes, percentage signs, exclamations, punctuation, hyphens, and special symbols.
ERASE_OR_REPLACE_TO_SPACE_SYMBOLS = re.compile(r'''[/\\%!！.?？^*·•⦁\-]''')

# A regular expression to match entity names that start with "the" followed by alphanumeric characters, case-insensitive.
THE_SPECIAL_ENTITY_NAME_REGEX = re.compile(r'^(the\s+[a-z0-9]+)$', re.IGNORECASE)

# A regular expression to match sequences of single letters separated by spaces (e.g., "a b c") and find those patterns, case-insensitive.
SINGLE_LETTER_SEQUENTIAL_REGEX = re.compile(rf'(\b[a-z]\b)(\s+[a-z]\b)+', re.IGNORECASE)

# A regular expression to match single lowercase letters surrounded by spaces (e.g., " a ").
SINGLE_LOWERCASE_REGEX = re.compile(rf'\s+[a-z]\s+')

# A regular expression to match and remove invalid symbols in company names, such as punctuation, special characters, and spaces around hyphens.
REGEX_COMPANY_DROP_INVALID = re.compile(r'[~$()@—－（）√《》:;：；.、•·‧・，*?+&|,/\[\\]|{}\t\n"]|([-]+\s|\s[-]+)')

# A regular expression to match symbols that should be replaced with spaces, including ampersands, question marks, asterisks, parentheses, commas, and hyphens.
REPLACE_TO_SPACE_SYMBOLS = re.compile(r'[&?#*|=_+()（）、,，–]')

class NameNormalizer:
    """
    This class handles the normalization of names, including circumflex letters and symbols.
    """

    # Pairing circumflex letters with their normalized counterparts
    CIRCUMFLEX_PAIRS = (
        (r'àâáãāåäǎ', 'a'), (r'ÀÂÁÃĀÅÄǍ', 'A'), (r'ß', 'b'), (r'čćç', 'c'), (r'ČÇ', 'C'),
        (r'ðđ', 'd'), (r'ÐĐ', 'D'), (r'éěèêëėệē', 'e'), (r'ÉÈÊËĖỆĒ', 'E'), (r'ğ', 'g'),
        (r'Ğ', 'G'), (r'îïíīịìǐĩı', 'i'), (r'İÎÏÍĪỊÌǏ', 'I'), (r'Ł', 'L'), (r'ł', 'l'),
        (r'ñňń', 'n'), (r'ÑŇŃ', 'N'), (r'ôöōồǒóòøőõ', 'o'), (r'ÔÖŌỒÓÒØŐÕ', 'O'), (r'ŕ', 'r'),
        (r'şš', 's'), (r'ŠŞ', 'S'), (r'ť', 't'), (r'ûùüúǔưū', 'u'), (r'ÛÙÜÚƯŪ', 'U'),
        (r'ŵ', 'w'), (r'ý', 'y'), (r'Ý', 'Y'), (r'žź', 'z'), (r'ŽŹ', 'Z'), (r'æ', 'ae'), (r'Æ', 'AE')
    )

    # Compile regex for circumflex replacements
    CIRCUMFLEX_REGEX_PAIRS = tuple(
        (re.compile(rf'[{regex_}]'), format_) for (regex_, format_) in CIRCUMFLEX_PAIRS
    )

    @classmethod
    def circumflex_regulator(cls, name: str) -> str:
        """
        Normalize circumflex letters in the name, e.g., 'é' becomes 'e'.
        If name is not a string, return an empty string.
        """
        if not isinstance(name, str) or pd.isna(name):
            return ''

        # Replace circumflex letters using pre-compiled regex pairs
        for regex_, format_character in cls.CIRCUMFLEX_REGEX_PAIRS:
            name = regex_.sub(format_character, name)
        return name


class CompanyMatcher:
    """
    This class handles company name matching using various techniques like tokenization, symbol regulation,
    and name normalization.
    """
    # Define common words for both English and Chinese
    COMPANY_COMMON_WORDS = {
        "en": {
            "laboratory", "laboratories", "lab", "labs", "research", "technology", "technologies",
            "technical", "tech", "sci", "science"
        },
        "zh": {
            "实验室", "研究院", "技术", "科技"
        }
    }
    COMPANY_KEYWORDS_REGEX = re.compile(
        r'\b(bank|college|university|education|energy|finance|army|air foce|navy|industry|'
        r'hospital|hotel|institutes?|institution|petroleum|oil|health|electronic|commercial|'
        r'environmental|gover(?:nor?|ment)|state|estado|procter|reliance|genome|software|hardware|agency|'
        r'(?:sou|nor)th(?:[-\s]?(?:ea|we)st(?:ern)?)?|[东西南北]方|[东西][南北][方]?|环境|'
        r'银行|软件|硬件|大学|机构|研究院|学院|教育|协会|能源|金融|旅馆|医院|石油|电子|工业|[陆海空]军|政府|基因|'
        r'global|market(?:ing)?|real estate|system|房地产|系统|兴业)\b',
        re.IGNORECASE)

    # Compile regex pattern for matching common words in company names
    COMPANY_COMMON_WORDS_REGEX = re.compile(
        r"{0}|{1}".format(
            '|'.join(COMPANY_COMMON_WORDS['zh']),
            rf"(\b|^)({'|'.join(COMPANY_COMMON_WORDS['en'])})(\.|\b|$)"
        ), re.I
    )
    # Define ranges for CJK (Chinese, Japanese, Korean) characters
    CJK_CHARACTERS = r'\u1100-\u11ff\u2e80-\u2fff\u3040-\u31ff\u3400-\u9fff\ua960-\ua97f\uac00-\ud7ff\uf900-\ufaff'

    # Regex to match CJK characters or numeric patterns
    CJK_OR_NUMERIC_REGEX = re.compile(
        rf"(?P<cjk>[{CJK_CHARACTERS}]+)|(?P<numeric>((?<=^\D)|(?<=[^\W0-9_]|\s))(?<!\b[a-zA-Z])(\d+([\W_]{{0,5}}\d+){{0,5}})(?=($|[^\W0-9_]|\s)))"
    )

    WHITESPACE_REGEX = re.compile(r'\s+')

    # Common prepositions
    PREPOSITION_WORDS = {
        'aboard', 'about', 'above', 'across', 'after', 'against', 'along', 'amid', 'among', 'anti', 'around', 'as',
        'at',
        'before', 'behind', 'below', 'beneath', 'beside', 'besides', 'between', 'beyond', 'but', 'by',
        'concerning', 'considering', 'despite', 'down', 'during', 'except', 'excepting', 'excluding', 'following',
        'for', 'from', 'in', 'inside', 'into', 'like', 'minus', 'near', 'of', 'off', 'on', 'onto', 'opposite',
        'outside', 'over', 'past', 'per', 'plus', 'regarding', 'round', 'since', 'than', 'through', 'till', 'to',
        'toward', 'towards', 'under', 'underneath', 'unlike', 'until', 'up', 'upon', 'versus', 'via', 'with', 'within',
        'without'
    }

    # Common conjunctions
    CONJUNCTIONS_WORDS = {
        "although", "because", "before", "both", "and", '&', "whether", "or", "either", "neither", "nor", "once",
        "just", "so", "as", "if", "then", "rather", "than", "till", 'when', 'where', 'whenever', 'while', 'wherever',
        "such", "so", "that"
    }

    # Common articles
    ARTICLES = {'a', 'an', 'the'}

    # Merge all irrelevant words (prepositions, conjunctions, articles, etc.)
    INLINE_WORDS = {
                       'also', 'am', 'are', 'did', 'furthermore', 'has', 'hence', 'how', 'however', 'includ.',
                       'instead', 'is', 'likewise',
                       'long', 'moreover', 'should', 'similar', 'though', 'thus', 'unless', 'was', 'were', 'what',
                       'which', 'whichever',
                       'why', 'will',
                       # Portugese prepositions
                       'de', 'di', 'em', 'del', 'des', 'do',
                       # 意大利语介词
                       'delle',
                       # Spanish prepositions
                       'con', 'sobre', 'en', 'contra', 'desde', 'entre', 'hacia', 'por', 'la',
                       # French prepositions
                       'apres', 'avant', 'avec', 'chez', 'contre', 'dans', 'depuis', 'derriere', 'devant', 'durant',
                       'envers', 'environ',
                       'jusque', 'malgre', 'par', 'parmi', 'pendant', 'pour', 'sans', 'selon', 'sous', 'suivant', 'sur',
                       'vers'
                   } | PREPOSITION_WORDS | CONJUNCTIONS_WORDS | ARTICLES

    # Common suffixes in company names (e.g. Ltd, Company, etc.)
    ORG_SUFFIX_WORDS = {
        'zh': {'common': ('公司', '集团', '有限公司', '有限责任公司', '股份有限公司'),
               'uncommon': ('总公司', '股份', '控股', '责任', '有限', '企业', '协会', '合作社', '株式会社')},
        'en': {'common': ('company', 'group', 'corporation', 'incorporated', 'enterprise', 'enterprises',
                          'co', 'inc', 'corp', 'ltd', 'llc', 'se', 'pvt'),
               'uncommon': ('corporation limited', 'companies', 'worldwide', 'limited', "holding", "holdings",
                            'com', 'gmbh', 'ag', 'plc', 'sal', 'spa', r's\.p\.a', 'sab cv', 'sa', 'nv', r'n\.v', 'lp',
                            'sro',
                            'kg', 'aktiengesellschaft', 'de cv', 'ltda', "group of companies")}
    }
    REGEX_COMPANY_DROP_INVALID = re.compile(r'[~$()@—－（）√《》:;：；.、•·‧・，*?+&|,/\[\\]|{}\t\n"]|([-]+\s|\s[-]+)')
    # Compile regular expressions for matching company suffixes
    ORG_SUFFIX_REGEX = re.compile(
        r"{0}|{1}".format(
            '|'.join([rf'{suf}' for suf in ORG_SUFFIX_WORDS['zh']['uncommon'] + ORG_SUFFIX_WORDS['zh']['common']]),
            rf"(?:\b(?:{'|'.join([suf for suf in ORG_SUFFIX_WORDS['en']['uncommon'] + ORG_SUFFIX_WORDS['en']['common']])})(?:\.|$))"
        ),
        re.IGNORECASE
    )

    def __init__(self, company_data_file: str):
        self.company_data_file = company_data_file
        self.matcher = NameMatcher(remove_ascii=False, punctuations=False)
        self.matching_data = None

    def load_company_data(self) -> pd.DataFrame:
        """
        Load the company data from a JSON Lines (.jsonl) file into a pandas DataFrame.
        Ensures aliases and required search strings are properly formatted.

        Returns:
        - pd.DataFrame: DataFrame containing company data including names and aliases.
        """
        companies = []
        with open(self.company_data_file, 'r', encoding='utf-8') as f:
            for line in f:
                company = json.loads(line)
                company['aliases'] = company.get('aliases', [])  # 确保别名存在
                companies.append(company)
        return pd.DataFrame(companies)

    def tokenize(self, text: str) -> str:
        """
        Tokenize the input text using Jieba for Chinese words and return the tokenized string.

        Parameters:
        - text (str): The text to tokenize (usually the company name).

        Returns:
        - str: Tokenized text.
        """
        # Use jieba to segment the text and concatenate the results with spaces into a string and return it
        return " ".join(jieba.cut(text))

    def search_string_regulator(self, name: str, return_str=True, is_company_name=False) -> str:
        """
        Regulate the search string to remove meaningless words and symbols. Handles both Chinese and English.

        :param name: The company name or string to regulate.
        :param return_str: If True, return the result as a string; otherwise, return as a list of words.
        :param is_company_name: Special flag to avoid removing certain common words for company names.
        """
        # Remove meaningless parts of the company name
        extracted_name = re.sub(r'[^\w\s]', '', name)  # Adjust this regex as per your needs
        if not extracted_name:
            return '' if return_str else []

        words = []
        # Split based on spaces or known separators
        for segment in extracted_name.split():
            if not segment:
                continue
            # If the segment is Chinese, treat it as a whole word
            if self.contains_chinese(segment):
                words.append(segment)
            # If it's a meaningful English word, keep it
            else:
                segment = segment.lower()
                if segment not in words or is_company_name:
                    words.append(segment)

        # Return as a single string or a list
        return ' '.join(words) if return_str else words

    def regulate_english_asians_mixed_string(self, text: str) -> str:
        """
        This function handles the regulation of mixed English and Asian (CJK) strings.
        It splits the input string into English, numbers, and CJK segments, then rejoins them.
        """
        # 调用 split_english_number_cjk 方法并传入正确的参数
        return ' '.join(self.split_english_number_cjk(text, separate_return=False))

    def split_english_number_cjk(self, text: str, separate_return: bool = True):
        """
        A utility function that splits text into English, numbers, and CJK (Chinese, Japanese, Korean) characters.
        This is a basic version to simulate the behavior.
        """
        import re
        CJK_REGEX = r'[\u4e00-\u9fff\uf900-\ufaff]+'  # Simplified regex to match CJK characters.
        EN_NUM_REGEX = r'[a-zA-Z0-9]+'

        cjk_parts = re.findall(CJK_REGEX, text)
        en_num_parts = re.findall(EN_NUM_REGEX, text)

        if separate_return:
            return en_num_parts, cjk_parts  # Return both parts separately
        else:
            return en_num_parts + cjk_parts  # Concatenate the parts if not separating

    def prepare_matching_data(self, companies: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data for matching, ensuring aliases and required search strings are correctly loaded as individual entries.
        """
        rows = []
        for _, company in companies.iterrows():
            # Process required search strings, ensure it's a list
            required_search_strings = company.get("requiredSearchStrings", [])
            if not isinstance(required_search_strings, list):
                required_search_strings = []  # If it's not a list, convert to empty list

            # Ensure aliases are also a list
            aliases = company.get("aliases", [])
            if not isinstance(aliases, list):
                aliases = []  # If it's not a list, convert to empty list

            # Combine required search strings and aliases into one list
            full_alias_list = required_search_strings + aliases

            # For each alias, create a separate row with all aliases as alias_name
            for alias in full_alias_list:
                rows.append({
                    "name": alias,
                    "companyName": company.get("companyName", ""),
                    "alias_name": full_alias_list,  # Store the full alias list
                    "is_alias": alias in aliases  # Mark if this is an alias
                })

        return pd.DataFrame(rows)

    def prepare_data_for_matching(self, companies: pd.DataFrame):
        """
        Prepare the company data for matching by tokenizing the names and loading them into the matcher.
        """
        companies['name'] = companies['name'].apply(self.tokenize)  # Tokenize company names
        self.matcher.load_and_process_master_data(column="name", df_matching_data=companies)

    def match_user_input(self, user_input: str, expected_name: str, threshold: int = 70) -> str:
        """
        Match user input against the company names, then validate against expected name.
        """

        # Input is NaN or non-string, convert it to an empty string
        if not isinstance(user_input, str) or pd.isna(user_input):
            user_input = ''

        # Call interpunction_regulator to process the symbols entered by the user
        user_input = self.interpunction_regulator(user_input)  # 处理符号
        if not user_input:
            return ''

        # Normalize and tokenize the input
        user_input_segmented = self.company_words_regulator(user_input)
        user_input_segmented = " ".join(jieba.cut(user_input_segmented))
        to_be_matched = pd.DataFrame({"name": [user_input_segmented]})

        # Matches the name entered by the user
        result = self.matcher.match_names(to_be_matched, column_matching="name")

        # No match, returns an empty string
        if result.empty:
            return ''

        # Get the best matching results
        best_match = result.iloc[0]["match_name"]
        match_score = result.iloc[0]["score"]

        # If the match score exceeds the threshold, it is considered a successful match.
        if match_score >= threshold:
            # 通过 best_match 查找公司名称和别名
            matched_row = self.matching_data[self.matching_data['name'] == best_match]
            if matched_row.empty:
                return ''

            # 获取公司名称和别名信息
            company_name = matched_row.iloc[0]['companyName']
            aliases = matched_row.iloc[0]['alias_name']  # 这现在是一个包含所有别名的列表

            # 处理 expected_name，防止 NaN 导致错误
            if pd.isna(expected_name):
                expected_name = ""  # 如果是 NaN，替换为空字符串
            else:
                expected_name = expected_name.lower()

            # 检查 expected_name 是否在别名中
            if expected_name and expected_name in [alias.lower() for alias in aliases]:
                return expected_name

            # 如果 expected_name 和 company_name 匹配，返回公司名称
            if expected_name == company_name.lower():
                return company_name

            # 如果没有匹配到 expected_name，默认返回公司名称
            return company_name
        else:
            return ''

    @staticmethod
    def contains_chinese(text: str) -> bool:
        """
        Check if the input text contains any Chinese characters.
        """
        CHINESE_CHARACTERS = r'\u2e80-\u2fff\u31c0-\u31ef\u3400-\u9fff\uf900-\ufaff'
        return bool(re.search(f"[{CHINESE_CHARACTERS}]", text))

    def company_words_regulator(self, company_name: str) -> str:
        """
        Clean up and regulate the company name by applying normalization rules for circumflexes, symbols,
        removing unnecessary company suffixes, and common words.
        """
        # Step 1: Normalize circumflex letters and process interpunction
        search_str = self.interpunction_regulator(NameNormalizer.circumflex_regulator(company_name))

        if not search_str:
            return ''

        # Step 2: Check if the string contains Chinese and process accordingly
        if self.contains_chinese(search_str):
            if not re.search(r"[a-zA-Z]", search_str):
                search_str = search_str.replace(' ', '')

        # Step 3: Remove company suffixes like 'inc', 'corp', etc., potentially twice to handle two occurrences
        search_str_drop = self.WHITESPACE_REGEX.sub(' ', self.ORG_SUFFIX_REGEX.sub('', self.ORG_SUFFIX_REGEX.sub('',
                                                                                                                 search_str).strip())).strip()

        # The string becomes empty after removing the suffixes, return an empty string
        if not search_str_drop:
            return ''

        # Step 4: Remove stock exchange abbreviations, e.g., 'SSE plc', 'NYSE', 'NASDAQ'
        search_str_drop_bourse = self.COMPANY_COMMON_WORDS_REGEX.sub(' ', search_str_drop).strip()
        if search_str_drop_bourse:
            search_str_drop = search_str_drop_bourse

        # Step 5: Remove common company words like 'technology', 'research', etc.
        search_str_drop_common_word = self.WHITESPACE_REGEX.sub(' ', self.COMPANY_COMMON_WORDS_REGEX.sub('',
                                                                                                         search_str_drop)).strip()
        if search_str_drop_common_word:
            search_str_drop = search_str_drop_common_word

        # Step 6: Ensure that removing common words doesn't leave just a keyword, e.g., 'Corporation Bank'
        if (r_ := self.COMPANY_KEYWORDS_REGEX.search(search_str_drop)) and r_.end() - r_.start() > len(
                search_str_drop) - 2:
            pass
        elif search_str == search_str_drop:
            pass
        else:
            search_str = search_str_drop

        # Step 7: Further regulate the search string and convert to lowercase
        search_str_regulate = self.search_string_regulator(search_str, is_company_name=True).lower()
        if search_str_regulate != search_str:
            search_str = search_str_regulate

        # Step 8: Remove invalid characters and filter valid words
        valid_words = []
        for word_ in search_str.split(' '):
            word_ = self.REGEX_COMPANY_DROP_INVALID.sub(' ', word_).strip().lower()
            if word_:
                valid_words.append(word_)

        # Return the cleaned and processed company name
        return ' '.join(valid_words)

    # Direct deletion symbols: '-' and '/'
    ERASE_SYMBOLS = re.compile(r'[-/]')



    def interpunction_regulator(self, name: str) -> str:
        """
        Regulates punctuation and symbols in the company name by:
        - Removing or replacing certain symbols with spaces.
        - Replacing special characters like '&' and '@' with words ('togetherwith', 'locatedat').
        - Handling special cases like sequential single letters and 'the' followed by a short word.
        """
        is_chinese = self.contains_chinese(name)

        if not is_chinese:
            # If name contains specific symbols, split and take the first word for further matching
            if name_words := re.split(r'[|]+', name):
                name = name_words[0]

        # Replace '&' with 'togetherwith' and '@' with 'locatedat'
        if and_match := re.search(r'&', name):
            name = name.replace('&', 'togetherwith')
        if at_match := re.search(r'@', name):
            name = name.replace('@', 'locatedat')

        # Replace specific symbols with spaces
        name = REPLACE_TO_SPACE_SYMBOLS.sub(' ', name)

        # Use ERASE_OR_REPLACE_TO_SPACE_SYMBOLS instead of ERASE_SYMBOLS
        if is_chinese:
            name = ERASE_OR_REPLACE_TO_SPACE_SYMBOLS.sub(' ', name).strip()
        else:
            name = ERASE_OR_REPLACE_TO_SPACE_SYMBOLS.sub('', name).strip()

        # Handle special cases for names starting with 'the' followed by a short word
        if the_match := THE_SPECIAL_ENTITY_NAME_REGEX.search(name):
            connect_str = the_match.group(1)
            name = name.replace(connect_str, re.sub(r'[\s]+', 'thespecial', connect_str))

        # Merge sequential single letters into one
        before_merge_name = name
        name = ''
        while True:
            if not (single_letter_sequential := SINGLE_LETTER_SEQUENTIAL_REGEX.search(before_merge_name)):
                name += before_merge_name.strip()
                break
            name += before_merge_name[
                    :single_letter_sequential.start()].strip() + ' ' + single_letter_sequential.group().replace(' ',
                                                                                                                '') + ' '
            before_merge_name = before_merge_name[single_letter_sequential.end():]

        # Drop single lowercase letters, but not if they are at the start or end
        name = SINGLE_LOWERCASE_REGEX.sub(' ', name)

        if is_chinese:
            name = self.regulate_english_asians_mixed_string(name)

        return name if name else None


def main():
    """
    Main function to initialize CompanyMatcher, load company data, and perform company name matching.
    """
    # Initialize CompanyMatcher and pass in the path to the company data file
    company_matcher = CompanyMatcher('bd_companies_international.jsonl')

    # Load Company Data
    companies = company_matcher.load_company_data()

    # Prepare matching data and organize company name and alias information into a format that can be matched
    matching_data = company_matcher.prepare_matching_data(companies)
    company_matcher.matching_data = matching_data

    # Prepare company data for matching (e.g. word segmentation)
    company_matcher.prepare_data_for_matching(matching_data)

    # Get input from the user and match the company name
    user_input = input("Enter a company name for matching: ")

    # Using a matcher to perform company name matching
    matched_company = company_matcher.match_user_input(user_input, expected_name=None)

    if matched_company:
        print(f"Matched company: {matched_company}")
    else:
        print("")


if __name__ == "__main__":
    main()
