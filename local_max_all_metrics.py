from pathlib import Path
from collections import defaultdict
import os
CORPUS_PATH = "./corpus4mw"
CORPUS_NAME = 'corpus4mw'

SPECIAL_CHARACTERS = [';', '.', ':', '!', '?', '<', '>',
                      '&', '(', ')', '[', ']', '\n', ',',
                      '}', '{', "'", '"', '-', '\\', '/',
                      '+', '=', '~', '@', '`', '%', '#',
                      '£', '$', '^', '*', '_', '‘', '’']

def separate_special_tokens(string):
    for char in SPECIAL_CHARACTERS:
        string = string.replace(char, f" {char} ")
    return string

def tokenize(string):
    tokens = separate_special_tokens(string).lower().split(' ')
    # don't return empty strings
    return tuple(filter(None, tokens))

def calculate_absolute_n_gram_frequencies(corpus, n_gram_size):
    n_gram_freqs = defaultdict(lambda: defaultdict(float))
    for doc_name, doc in corpus.items():
        for i in range(len(doc) - n_gram_size):
            n_gram = doc[i: i + n_gram_size]
            n_gram_freqs[n_gram]["abs_freq"] += 1
    return n_gram_freqs

def calculate_n_gram_frequencies(corpus, max_n_gram_size, corpus_size):
    n_gram_frequencies = dict()
    for n_gram_size in range(1, max_n_gram_size + 1):
        n_gram_frequencies[n_gram_size] = calculate_absolute_n_gram_frequencies(corpus, n_gram_size)
        for freq in n_gram_frequencies[n_gram_size].values():
            freq["rel_freq"] = freq["abs_freq"] / corpus_size
    return n_gram_frequencies

def minimum_frequency_filter(n_gram_freq_dict, min_freq):
    filtered_n_gram_freq_dict = dict()
    for n_gram_size in n_gram_freq_dict:
        filtered_n_gram_freq_dict[n_gram_size] = defaultdict(lambda: defaultdict(float))
        for n_gram, n_gram_freq in n_gram_freq_dict[n_gram_size].items():
            if n_gram_freq["abs_freq"] >= min_freq:
                filtered_n_gram_freq_dict[n_gram_size][n_gram] = n_gram_freq_dict[n_gram_size][n_gram]
    return filtered_n_gram_freq_dict

def special_characters_filter(n_gram_freq_dict, special_characters):
    filtered_n_gram_freq_dict = dict()
    for n_gram_size in n_gram_freq_dict:
        filtered_n_gram_freq_dict[n_gram_size] = defaultdict(lambda: defaultdict(float))
        for n_gram, n_gram_freq in n_gram_freq_dict[n_gram_size].items():
            if not any(sc for sc in special_characters if sc in n_gram):
                filtered_n_gram_freq_dict[n_gram_size][n_gram] = n_gram_freq_dict[n_gram_size][n_gram]
    return filtered_n_gram_freq_dict

def calculate_absolute_frequency_of_n_gram(n_gram, n_gram_freq_dict):
    return n_gram_freq_dict[len(n_gram)][n_gram]['abs_freq']

def calculate_relative_frequency_of_n_gram(n_gram, n_gram_freq_dict):
    return n_gram_freq_dict[len(n_gram)][n_gram]['rel_freq']

def lower_case_tuple(l):
    return tuple(item.lower() for item in l)

def scp_f(n_gram, n_gram_freq_dict):
    n_gram = lower_case_tuple(n_gram)
    if len(n_gram) == 1:
        #scp_f for unigrams is always 1 / not defined
        return 1
    p_squared = calculate_relative_frequency_of_n_gram(n_gram, n_gram_freq_dict)**2
    sum_relative_freq = 0
    for i in range(0,len(n_gram)-1):
        p = calculate_relative_frequency_of_n_gram(n_gram[:i+1], n_gram_freq_dict) * calculate_relative_frequency_of_n_gram(n_gram[i+1:], n_gram_freq_dict)
        sum_relative_freq = sum_relative_freq + p
    F = 1 / (len(n_gram) - 1) * sum_relative_freq
    if (F == 0):
        print(n_gram)
    scp_f = p_squared / F
    return scp_f

def dice_f(n_gram, n_gram_freq_dict):
    n_gram = lower_case_tuple(n_gram)
    abs_frequency = calculate_absolute_frequency_of_n_gram(n_gram, n_gram_freq_dict)
    sum_abs_freq = 0
    for i in range(0,len(n_gram)-1):
        f = calculate_absolute_frequency_of_n_gram(n_gram[:i+1], n_gram_freq_dict) * calculate_absolute_frequency_of_n_gram(n_gram[i+1:], n_gram_freq_dict)
        sum_abs_freq = sum_abs_freq + f
    F = 1 / (len(n_gram) - 1) * sum_abs_freq
    dice = (abs_frequency * 2) / F
    return dice

import math
def mi_f(n_gram, n_gram_freq_dict):
    n_gram = lower_case_tuple(n_gram)
    relative_frequency = calculate_relative_frequency_of_n_gram(n_gram, n_gram_freq_dict)
    sum_relative_freq = 0
    for i in range(0,len(n_gram)-1):
        p = calculate_relative_frequency_of_n_gram(n_gram[:i+1], n_gram_freq_dict) * calculate_relative_frequency_of_n_gram(n_gram[i+1:], n_gram_freq_dict)
        sum_relative_freq = sum_relative_freq + p
    F = 1 / (len(n_gram) - 1) * sum_relative_freq
    mi = math.log(relative_frequency / F)
    return mi

def calculate_containing_and_contained_n_grams(n_gram_freq_dict, max_n_gram_size):
    containing_n_grams = defaultdict(list)
    contained_n_grams = defaultdict(list)
    
    # we don't calculate contained n-grams for unigrams
    for n_gram_size in range(2, max_n_gram_size + 1):
        for n_gram in n_gram_freq_dict[n_gram_size]:

            # calculate contained n-grams
            left_contained_n_gram = n_gram[0: -1]
            right_contained_n_gram = n_gram[1:]

            contained_n_grams[n_gram] = [left_contained_n_gram, right_contained_n_gram]
            containing_n_grams[left_contained_n_gram].append(n_gram)
            containing_n_grams[right_contained_n_gram].append(n_gram)
    
    return containing_n_grams, contained_n_grams

import itertools 

def calculate_local_max_fixed_size(re_size, n_gram_freq_dict, containing_n_grams_dict, contained_n_grams_dict, glue):
    relevant_expressions = []
    
    if re_size == 2:
        for n_gram in n_gram_freq_dict[re_size]:
            
            containing_n_grams = containing_n_grams_dict[n_gram]
            containing_n_grams_glues = [glue(containing_n_gram, n_gram_freq_dict) for containing_n_gram in containing_n_grams]
            n_gram_glue = glue(n_gram, n_gram_freq_dict)
            
            if all([n_gram_glue > containing_n_gram_glue for containing_n_gram_glue in containing_n_grams_glues]):
                relevant_expressions.append(n_gram)
            
    else:
        for n_gram in n_gram_freq_dict[re_size]:
            
            containing_n_grams = containing_n_grams_dict[n_gram]
            containing_n_grams_glues = [glue(containing_n_gram, n_gram_freq_dict) for containing_n_gram in containing_n_grams]
            
            # contained n_grams 
            contained_n_grams = contained_n_grams_dict[n_gram]
            contained_n_grams_glues = [glue(contained_n_gram, n_gram_freq_dict) for contained_n_gram in contained_n_grams]
            
            n_gram_glue = glue(n_gram, n_gram_freq_dict)
            
            if all(n_gram_glue > ((glues[0] + glues[1]) / 2) for glues in itertools.product(contained_n_grams_glues, containing_n_grams_glues)):
                relevant_expressions.append(n_gram)
        
    return relevant_expressions

corpus = defaultdict(tuple)

# open all files starting with "fil" in corpus path
for doc_path in Path(CORPUS_PATH).glob('fil_*'):
    
    # read whole document and strip new lines
    doc = Path(doc_path).read_text().replace('\n', '')
    # standardize space characters
    doc = doc.replace(u'\xa0', u' ').replace(u'\u3000', u' ').replace(u'\u2009', u' ')
    
    doc_name = os.path.basename(doc_path)
    corpus[doc_name] = tokenize(doc)

corpus_words = [word for doc_list in corpus.values() for word in doc_list]
corpus_size = len(corpus_words)

def local_max(corpus, max_re_size, n_gram_freq_dict, glue):
    # extract all relevant expressions of sizes up to max_re_size (inclusive) from corpus using glue function
    relevant_expressions = []
    
    containing_n_grams, contained_n_grams = calculate_containing_and_contained_n_grams(n_gram_freq_dict, max_re_size + 1)
    
    # local max is only defined for multi-grams
    for re_size in range(2, max_re_size + 1):
        relevant_expressions += calculate_local_max_fixed_size(re_size, n_gram_freq_dict, containing_n_grams, contained_n_grams, glue)
    
    return relevant_expressions

def stop_words_filter(corpus, relevant_expressions):
    #corpus_words = set(word for doc_list in corpus.values() for word in doc_list)
    
    neighbour_dict = defaultdict(set)
    
    for doc_name, doc in corpus.items():
        for word_index in range(0, len(doc)):
            
            word = doc[word_index]
            
            if word_index != 0:
                right_neighbour = doc[word_index - 1]
                neighbour_dict[word].add(right_neighbour)
            if word_index != len(doc) - 1:
                left_neighbour = doc[word_index + 1]
                neighbour_dict[word].add(left_neighbour)
            
    neighbour_counts = []
    
    for word, neighbours in neighbour_dict.items():
        neighbour_counts.append((len(neighbours), word))
        
    neighbour_counts.sort(reverse=True)
    
    # find elbow point
    elbow_point_index = 0
    max_tangens = 0
    for index in range(0, len(neighbour_counts) - 1):
        cur_neighbour_count = neighbour_counts[index][0]
        next_neighbour_count = neighbour_counts[index + 1][0]
        neighbour_diff = cur_neighbour_count - next_neighbour_count #list is sorted decreasing
        tangens_diff = abs(math.tan(cur_neighbour_count + neighbour_diff) - math.tan(cur_neighbour_count))
        
        if tangens_diff > max_tangens:
            elbow_point_index = index
            max_tangens = tangens_diff
    
    stop_word_counts = neighbour_counts[: elbow_point_index + 1]
    
    stop_words = [stop_word_count[1] for stop_word_count in stop_word_counts]
    
    filtered_relevant_expressions = []
    for re in relevant_expressions:
        if re[0] in stop_words or re[-1] in stop_words:
            continue
        filtered_relevant_expressions.append(re)
    
    return stop_words, filtered_relevant_expressions