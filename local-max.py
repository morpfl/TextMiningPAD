words = []

for i in range(0,5359):
    print('reading file', i+1, end='\r')
    try:
        with open('./corpus2mw/fil_' + str(i+1)) as file:
            for line in file:
                if ';' in line:
                    char_index = line.index(';')
                    line = line[:char_index+1] + ' ' + line[char_index+1:] 
                    line = line[:char_index] + ' ' + line[char_index:]
                if '.' in line:
                    char_index = line.index('.')
                    line = line[:char_index+1] + ' ' + line[char_index+1:] 
                    line = line[:char_index] + ' ' + line[char_index:]
                if ':' in line:
                    char_index = line.index(':')
                    line = line[:char_index+1] + ' ' + line[char_index+1:] 
                    line = line[:char_index] + ' ' + line[char_index:]
                if '!' in line:
                    char_index = line.index('!')
                    line = line[:char_index+1] + ' ' + line[char_index+1:] 
                    line = line[:char_index] + ' ' + line[char_index:]
                if '?' in line:
                    char_index = line.index('?')
                    line = line[:char_index+1] + ' ' + line[char_index+1:] 
                    line = line[:char_index] + ' ' + line[char_index:]
                if '<' in line:
                    char_index = line.index('<')
                    line = line[:char_index+1] + ' ' + line[char_index+1:] 
                    line = line[:char_index] + ' ' + line[char_index:]
                if '>' in line:
                    char_index = line.index('>')
                    line = line[:char_index+1] + ' ' + line[char_index+1:] 
                    line = line[:char_index] + ' ' + line[char_index:]
                if '&' in line:
                    char_index = line.index('&')
                    line = line[:char_index+1] + ' ' + line[char_index+1:] 
                    line = line[:char_index] + ' ' + line[char_index:]
                if '(' in line:
                    char_index = line.index('(')
                    line = line[:char_index+1] + ' ' + line[char_index+1:] 
                    line = line[:char_index] + ' ' + line[char_index:]
                if ')' in line:
                    char_index = line.index(')')
                    line = line[:char_index+1] + ' ' + line[char_index+1:] 
                    line = line[:char_index] + ' ' + line[char_index:]
                if '[' in line:
                    char_index = line.index('[')
                    line = line[:char_index+1] + ' ' + line[char_index+1:] 
                    line = line[:char_index] + ' ' + line[char_index:]
                if ']' in line:
                    char_index = line.index(']')
                    line = line[:char_index+1] + ' ' + line[char_index+1:] 
                    line = line[:char_index] + ' ' + line[char_index:]
                if '\n' in line:
                    char_index = line.index('\n')
                    line = line[:char_index+1] + ' ' + line[char_index+1:] 
                    line = line[:char_index] + ' ' + line[char_index:]
                words.extend(line.split(' '))
    except OSError as e:
        continue
print('Words with escaped special characters: ', len(words))
words = list(filter(lambda x: x != '' and x != ';' and x != ':' and x != '!' and x != '?' and x != '<' and x != '>' and x != '(' and x != ')' and x != ']' and x != '[' and x != '\n', words))
print('Words cleaned: ', len(words))

def calculate_relative_frequency_of_nGram(nGram):
    nGramOccurrenceInCorpus = len([nGram for idx in range(len(words)) if words[idx : idx + len(nGram)] == nGram])
    p = nGramOccurrenceInCorpus / len(words)
    return p

def scp_f(nGram):
    p_squared = calculate_relative_frequency_of_nGram(nGram)**2
    sum_relative_freq = 0
    for i in range(0,len(nGram)-1):
        p = calculate_relative_frequency_of_nGram(nGram[:i+1]) * calculate_relative_frequency_of_nGram(nGram[i+1:])
        sum_relative_freq = sum_relative_freq + p
    F = 1 / (len(nGram) - 1) * sum_relative_freq
    scp_f = p_squared / F
    return scp_f

#TODO: Implementing some more coherence measures

def localMax(n, lookup_word):
    relevantNGrams = []
    # get all the nGrams, filtering is necessary, as there are sublists with less than n elements at the end of the corpus
    allNGrams = list(filter(lambda l: len(l) == n, [words[i:i+n] for i in range(0, len(words))]))
    allNGramsFiltered = list(filter(lambda l: lookup_word in l, allNGrams))
    for nGram in allNGramsFiltered:
        print('N-Gram', allNGramsFiltered.index(nGram), '/', len(allNGramsFiltered))
        # all (n-1)-grams contained by original n-gram
        smallerNGrams = list(filter(lambda l: len(l) == n-1, [nGram[i:i+(n-1)] for i in range(0, len(nGram))]))
        # all (n+1)-grams of corpus
        largerNGrams = list(filter(lambda l: len(l) == n+1, [words[i:i+(n+1)] for i in range(0, len(words))]))
        # all the (n+1)-grams containing the original nGram
        largerNGrams = list(filter(lambda s: any(s[idx : idx + len(nGram)] == nGram for idx in range(0,2)), largerNGrams))

        scp_f_nGram = scp_f(nGram)
        scpValuesOfSmallerNGrams = list(map(lambda n: scp_f(n), smallerNGrams))

        # !! Here is our problem... Usually we have many larger n+1 grams, and calculating the scp takes time !!
        scpValuesOfLargerNGrams = list(map(lambda n: scp_f(n), largerNGrams))

        nGramIsRelevantExpressionCheck1 = False
        nGramIsRelevantExpressionCheck2 = True

        if len(nGram) == 2:
            nGramIsRelevantExpressionCheck1 = all(y <= scp_f_nGram for y in scpValuesOfLargerNGrams)
        if len(nGram) > 2:
            for scpOfSmallerNGram in scpValuesOfSmallerNGrams:
                for scpOfLargerNGram in scpValuesOfLargerNGrams:
                    sumOfScpValues = scpOfLargerNGram + scpOfSmallerNGram
                    if scp_f_nGram <= sumOfScpValues / 2:
                        nGramIsRelevantExpressionCheck2 = False
                        break        
        if nGramIsRelevantExpressionCheck1 or nGramIsRelevantExpressionCheck2: 
            relevantNGrams.append(nGram)
            print(nGram, 'is relevant expression')
        else:
            print(nGram, 'is not a relevant expression.')

    return relevantNGrams

rNGrams = localMax(4, 'America')