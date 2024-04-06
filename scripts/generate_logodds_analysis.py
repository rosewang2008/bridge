import os
import sys
sys.path.append(os.getcwd())
from scripts.constants import LOGODDS_DIR
import json
import pandas as pd
from nltk.corpus import stopwords
import itertools
from scripts import language_analysis_utils
from gensim.models import Phrases
from gensim.models.phrases import Phraser 
from gensim.parsing.preprocessing import remove_stopwords

TEXT_COLUMN = language_analysis_utils.TEXT_COLUMN
CLEAN_TEXT_COLUMN = language_analysis_utils.CLEAN_TEXT_COLUMN
BIGRAM_COLUMN = "bigrams"
NGRAM_COLUMN = "ngrams"
CLEANED_NGRAM_TEXT_COLUMN = "cleaned_ngram_text"
CLEANED_NGRAM_TEXT_AS_LIST_COLUMN = "cleaned_ngram_text_as_list"

stopwords = set(stopwords.words('english'))

import nltk
import re
from nltk.corpus import stopwords
import string

punct_chars = list((set(string.punctuation) | {'»', '–', '—', '-',"­", '\xad', '-', '◾', '®', '©','✓','▲', '◄','▼','►', '~', '|', '“', '”', '…', "'", "`", '_', '•', '*', '■'} - {"'"}))
punct_chars.sort()
punctuation = ''.join(punct_chars)
replace = re.compile('[%s]' % re.escape(punctuation))
sno = nltk.stem.SnowballStemmer('english')
printable = set(string.printable)


def clean_text(text,
               remove_stopwords=True,
               remove_numeric=True,
               stem=False,
               remove_short=True,
               stopwords_file="wordlists/stopwords/en/mallet.txt"):
    # lower case
    text = text.lower()
    # eliminate urls
    text = re.sub(r'http\S*|\S*\.com\S*|\S*www\S*', ' ', text)
    # substitute all other punctuation with whitespace
    text = replace.sub(' ', text)
    # replace all whitespace with a single space
    text = re.sub(r'\s+', ' ', text)
    # strip off spaces on either end
    text = text.strip()
    # make sure all chars are printable
    text = ''.join([c for c in text if c in printable])
    words = text.split()
    if remove_stopwords:
        stopwords = open(stopwords_file, "r").read().splitlines()
        words = [w for w in words if w not in stopwords]
    if remove_numeric:
        words = [w for w in words if not w.isdigit()]
    if stem:
        words = [sno.stem(w) for w in words]
    if remove_short:
        words = [w for w in words if len(w) >= 3]
    return words

def build_df(json_path, key):
    with open(json_path, 'r') as f:
        revisions = json.load(f)

    shortname = os.path.basename(json_path).split(".")[0]

    df = []
    for revision in revisions:

        df.append({
            'c_id': revision['c_id'],
            'shortname': shortname,
            TEXT_COLUMN: " ".join([_['text'] for _ in revision[key]]),
        })
        # Replace apostrophes
        df[-1][TEXT_COLUMN] = df[-1][TEXT_COLUMN].replace("'", "")
    df = pd.DataFrame(df)
    return df

def get_ngrams(text, n):
    return ["_".join(text[i:i+n]) for i in range(len(text)-n+1)]

def run_original_log_odds(group1_df, group2_df, setting, save_path):
    group1_df[CLEAN_TEXT_COLUMN] = group1_df[TEXT_COLUMN].apply(lambda x: language_analysis_utils.clean_text_to_words(x, keep_stopwords=True, stem=False))
    group2_df[CLEAN_TEXT_COLUMN] = group2_df[TEXT_COLUMN].apply(lambda x: language_analysis_utils.clean_text_to_words(x, keep_stopwords=True, stem=False))

    group1_df[CLEANED_NGRAM_TEXT_AS_LIST_COLUMN] = group1_df[TEXT_COLUMN].apply(
        lambda x: [clean_text(remove_stopwords(_), remove_stopwords=False, remove_numeric=True) for _ in nltk.sent_tokenize(x)]
    )
    group1_df[CLEANED_NGRAM_TEXT_COLUMN] = group1_df[CLEANED_NGRAM_TEXT_AS_LIST_COLUMN].apply(
        # Merge lists of lists -> list of strings
        lambda x: list(itertools.chain.from_iterable(x))
    )
    cleaned_sents1 = list(itertools.chain.from_iterable(group1_df[CLEANED_NGRAM_TEXT_AS_LIST_COLUMN].tolist())) 

    group2_df[CLEANED_NGRAM_TEXT_AS_LIST_COLUMN] = group2_df[TEXT_COLUMN].apply(
        lambda x: [clean_text(remove_stopwords(_), remove_stopwords=False, remove_numeric=True) for _ in nltk.sent_tokenize(x)]
    )
    group2_df[CLEANED_NGRAM_TEXT_COLUMN] = group2_df[CLEANED_NGRAM_TEXT_AS_LIST_COLUMN].apply(
        # Merge lists of lists -> list of strings -> join into one string " "
        lambda x: list(itertools.chain.from_iterable(x))
    )
    cleaned_sents2 = list(itertools.chain.from_iterable(group2_df[CLEANED_NGRAM_TEXT_AS_LIST_COLUMN].tolist()))

    # Apply bigram on CLEANED_NGRAM_TEXT_COLUMN which is list of list.
    # First apply bigram on each list, then join into one list
    group1_df[BIGRAM_COLUMN] = group1_df[CLEANED_NGRAM_TEXT_AS_LIST_COLUMN].apply(lambda x: list(itertools.chain.from_iterable([get_ngrams(_, n=2) for _ in x])))
    group2_df[BIGRAM_COLUMN] = group2_df[CLEANED_NGRAM_TEXT_AS_LIST_COLUMN].apply(lambda x: list(itertools.chain.from_iterable([get_ngrams(_, n=2) for _ in x])))

    bigram_model = Phrases(cleaned_sents1 + cleaned_sents2, min_count=5) #, threshold=1)
    bigram_phraser = Phraser(bigram_model)
    group1_df[NGRAM_COLUMN] = group1_df[CLEANED_NGRAM_TEXT_COLUMN].apply(lambda x: bigram_phraser[x])
    group2_df[NGRAM_COLUMN] = group2_df[CLEANED_NGRAM_TEXT_COLUMN].apply(lambda x: bigram_phraser[x])

    print("Constructing bi-grams...")
    group1_words, _ = language_analysis_utils.get_log_odds(
        group1=group1_df, 
        group2=group2_df,
        text_column=BIGRAM_COLUMN, 
        logodds_factor=1.5,
    )

    # Output top 10 bigrams with logodds to save_path
    text = "Top 10 bigrams:\n"
    count = 0
    for i, row in group1_words.iterrows():
        # Round to 2 decimal places
        logodds = round(row['log_odds'], 2)
        text += f"{i}: {logodds}\n"
        count += 1
        if count == 10:
            break

    with open(save_path, "w") as f:
        f.write(text)

    print(f"Saved to {save_path}")

if __name__ == "__main__":
    TEXT_KEY = "c_r_"
    models = [
        ("gpt4", "GPT4"),
        ("chatgpt", "ChatGPT"),
        ("llama-2-70b-chat", "Llama-2-70b-Instruct"),
    ]
    settings = [
        {
            "name": "No Decisions + Model",
            "group1": ["outputs/responses/none_{model_shortname}.json"], 
            "group2": [
                "outputs/responses/expert_{model_shortname}.json", 
                "outputs/responses/{model_shortname}_{model_shortname}.json", 
                "outputs/responses/random_{model_shortname}.json",
                ],
        },
        {
            "name": "Expert Decisions + Model",
            "group1": ["outputs/responses/expert_{model_shortname}.json"], 
            "group2": [
                "outputs/responses/none_{model_shortname}.json",
                "outputs/responses/{model_shortname}_{model_shortname}.json",
                "outputs/responses/random_{model_shortname}.json",
                ]
        },
        {
            "name": "Self Decisions + Model",
            "group1": ["outputs/responses/{model_shortname}_{model_shortname}.json"], 
            "group2": [
                "outputs/responses/none_{model_shortname}.json",
                "outputs/responses/expert_{model_shortname}.json", 
                "outputs/responses/random_{model_shortname}.json",
                ]
        },
        {
            "name": "Random Decisions + Model",
            "group1": ["outputs/responses/random_{model_shortname}.json"], 
            "group2": [
                "outputs/responses/none_{model_shortname}.json",
                "outputs/responses/expert_{model_shortname}.json", 
                "outputs/responses/{model_shortname}_{model_shortname}.json"
                ]
        }
    ]


    for model in models:
        for setting in settings: 
            save_path = os.path.join(
                LOGODDS_DIR,
                f"{model[0]}_{setting['name'].replace(' ', '_')}.txt"
            )

            # Build dataframes
            df1 = []
            for group1_name in setting['group1']:
                df1.append(build_df(group1_name.format(model_shortname=model[0]), TEXT_KEY))
            group1_df = pd.concat(df1)

            df2 = []
            for group2_name in setting['group2']:
                df2.append(build_df(group2_name.format(model_shortname=model[0]), TEXT_KEY))
            group2_df = pd.concat(df2)

            # Run original log odds analysis
            run_original_log_odds(group1_df, group2_df, setting, save_path)

            # There a simpler implementation of logodds with Edu-ConvoKit. 
            # It won't return the same result though because it cleans the text differently.
            # import edu_convokit.analyzers as LexicalAnalyzer
            # lexical_analyzer = LexicalAnalyzer()
            # lexical_analyzer.print_log_odds(df1=group1_df, df2=group2_df, text_column1='text', text_column2='text', run_text_formatting=True, run_ngrams=True, n=2, topk=10)
