import re

ENGLISH_SPLITTER_REGEX = re.compile(r"[^\w&_+*\\/'#\-]+")
CJK_CHARACTERS = r'\u1100-\u11ff\u2e80-\u2fff\u3040-\u31ff\u3400-\u9fff\ua960-\ua97f\uac00-\ud7ff\uf900-\ufaff'
CJK_OR_NUMERIC_REGEX = re.compile(rf"(?P<cjk>[{CJK_CHARACTERS}]+)|(?P<numeric>((?<=^\D)|(?<=[^\W0-9_]|\s))(?<!\b[a-zA-Z])(\d+([\W_]{{0,5}}\d+){{0,5}})(?=($|[^\W0-9_]|\s)))")


def split_english_number_cjk(text: str, separate_return=False, split_same_language=False):
    """
    Chinese and Chinese-English Mixture Operations
    :param text: e.g. "non_asians string: 并删除掉Machine-learning多余的, 字符串"
    :param separate_return: False
    :param split_same_language: False
    :return: e.g. ["non_asians string:", "并删除掉", "Machine-learning", "多余的, 字符串"]
    :param separate_return: False
    :param split_same_language: True
    :return: e.g. ['non_asians', 'string', '并', '删', '除', '掉', 'Machine-learning', '多', '余', '的', '字', '符', '串']
    :param separate_return: True
    :param split_same_language: False
    :return: e.g. (["non_asians string:", "Machine-learning"], ["并删除掉", "多余的, 字符串"])
    :param separate_return: True
    :param split_same_language: True
    :return: e.g. (['non_asians', 'string', 'Machine-learning'], ['并', '删', '除', '掉', '多', '余', '的', '字', '符', '串'])
    """
    en_number_words = []
    cjk_words = []
    start, end = 0, len(text)
    while start < end and (r_ := CJK_OR_NUMERIC_REGEX.search(text, pos=start)):
        # before word
        if word := text[start:r_.start()].strip():
            if split_same_language:
                en_number_words.extend(
                    [stripped_word for word_ in ENGLISH_SPLITTER_REGEX.split(word) if (stripped_word := word_.strip())])
            else:
                en_number_words.append(word)
        # matched word
        if cjk_word := r_.groupdict().get("cjk"):
            if split_same_language:
                (cjk_words if separate_return else en_number_words).extend(list(cjk_word))
            else:
                (cjk_words if separate_return else en_number_words).append(cjk_word)
        else:
            numeric_word = r_.groupdict().get("numeric")
            if split_same_language:
                en_number_words.extend([stripped_word for word_ in ENGLISH_SPLITTER_REGEX.split(numeric_word) if (stripped_word := word_.strip())])
            else:
                en_number_words.append(numeric_word)
        start = r_.end()

    # save after left words
    if end > start and (text := text[start:].strip()):
        if split_same_language:
            en_number_words.extend([word_ for word in ENGLISH_SPLITTER_REGEX.split(text) if (word_ := word.strip())])
        else:
            en_number_words.append(text)
    return (en_number_words, cjk_words) if separate_return else en_number_words
