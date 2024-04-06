import pandas as pd
from collections import defaultdict
import math
import re
import nltk
import string
import os
import sys
sys.path.append(os.getcwd())
CLEAN_TEXT_COLUMN = 'cleaned_text'
TEXT_COLUMN = 'text'

# Download nltk data
nltk.download('stopwords')
nltk.download('punkt')

sno = nltk.stem.SnowballStemmer('english')
punct_chars = list((set(string.punctuation) | {'’', '‘', '–', '—', '~', '|', '“', '”', '…', "'", "`", '_'}) - set(['#']))
punct_chars.sort()
punctuation = ''.join(punct_chars)
replace = re.compile('[%s]' % re.escape(punctuation))

stopwords = set(open(os.path.join(os.getcwd(), "scripts", "stopwords.txt"), 'r').read().splitlines())

def get_counts(tweets, vocab):
    counts = {w: 0 for w in vocab}
    for split in tweets:
        count = 0
        prev = ''
        for w in split:
            if w == '':
                continue
            if w in vocab:
                counts[w] += 1
            if count > 0:
                bigram = prev + ' ' + w
                if bigram in vocab:
                    counts[bigram] += 1
            count += 1
            prev = w
    return counts

def log_odds(counts1, counts2, prior, zscore = True):
    # code from Dan Jurafsky
    # note: counts1 will be positive and counts2 will be negative

    sigmasquared = defaultdict(float)
    sigma = defaultdict(float)
    delta = defaultdict(float)

    n1 = sum(counts1.values())
    n2 = sum(counts2.values())

    # since we use the sum of counts from the two groups as a prior, this is equivalent to a simple log odds ratio
    nprior = sum(prior.values())
    for word in prior.keys():
        if prior[word] == 0:
            delta[word] = 0
            continue
        l1 = float(counts1[word] + prior[word]) / (( n1 + nprior ) - (counts1[word] + prior[word]))
        l2 = float(counts2[word] + prior[word]) / (( n2 + nprior ) - (counts2[word] + prior[word]))
        sigmasquared[word] = 1/(float(counts1[word]) + float(prior[word])) + 1/(float(counts2[word]) + float(prior[word]))
        sigma[word] = math.sqrt(sigmasquared[word])
        delta[word] = (math.log(l1) - math.log(l2))
        if zscore:
            delta[word] /= sigma[word]
    return delta


def get_log_odds_values(group1_df, group2_df, text_column, words2idx):
    # get counts
    counts1 = get_counts(group1_df[text_column], words2idx)
    counts2 = get_counts(group2_df[text_column], words2idx)
    prior = {}
    for k, v in counts1.items():
        prior[k] = v + counts2[k]

    # get log odds
    # note: we don't z-score because that makes the absolute values for large events significantly smaller than for smaller
    # events. however, z-scoring doesn't make a difference for our results, since we simply look at whether the log odds
    # are negative or positive (rather than their absolute value)
    delta = log_odds(counts1, counts2, prior, True)
    return prior, counts1, counts2, delta


def clean_text_to_words(text, keep_stopwords, stem):
    if not keep_stopwords:
        stop = stopwords
    # lower case
    text = text.lower()
    # eliminate urls
    text = re.sub(r'http\S*|\S*\.com\S*|\S*www\S*', ' ', text)
    # eliminate @mentions
    text = re.sub(r'\s@\S+', ' ', text)
    # substitute all other punctuation with whitespace
    text = replace.sub(' ', text)
    # replace all whitespace with a single space
    text = re.sub(r'\s+', ' ', text)
    # strip off spaces on either end
    text = text.strip()
    # stem words
    words = text.split()
    if not keep_stopwords:
        words = [w for w in words if w not in stop]
    if stem:
        words = [sno.stem(w) for w in words]
    return words


def get_log_odds(group1, group2, text_column, logodds_factor=1.5):
  # Let's build a dictionary that maps all words from teacher and student to unique IDs
  words = group1[text_column].sum() + group2[text_column].sum()
  # Get unique words
  words = list(set(words))
  words2idx = {w: i for i, w in enumerate(words)}

  # Run log odds
  _, _, _, log_odds = get_log_odds_values(
    group1_df=group1,
    group2_df=group2,
    text_column=text_column,
    words2idx=words2idx
  )

  # Let's create a dataframe with the log odds values, and then plot the top and bottom 10 words in a barplot.
  log_odds_df = pd.DataFrame.from_dict(log_odds, orient='index', columns=['log_odds'])
  log_odds_df = log_odds_df.sort_values(by='log_odds', ascending=False)
  # Plot the words factor*std above and below 0.
  mean = 0
  std = log_odds_df['log_odds'].std()
  factor = logodds_factor
  top_bottom_df = pd.concat([log_odds_df[log_odds_df['log_odds'] >= mean + factor * std], log_odds_df[log_odds_df['log_odds'] <= mean - factor * std]])
  top_words = log_odds_df[log_odds_df['log_odds'] >= mean + factor * std] 
  bottom_words = log_odds_df[log_odds_df['log_odds'] <= mean - factor * std]

  return top_words, bottom_words
