'''
Corporate Sustainability Analysis
This code processes files uploaded to the project directory for total and categorical word counts and outputs graphs and csv files.
'''
import os
import matplotlib.pyplot as plt
from collections import defaultdict
import re
import csv

interest_words_file = open('words_of_interest.txt', 'r')
interest_words_lines = interest_words_file.readlines()
interest_words = {}
for line in interest_words_lines:
    words = [word.strip() for word in line.split(',')]
    interest_words[words[0]] = words[1:]
interest_words_file.close()

def process_file(report_file):
    #uses name of 10-k file to get the company name and year
    localFilePath = os.path.basename(report_file)
    fileName = localFilePath.split('_')
    company = fileName[0][:-8]
    report = '10-K'
    year = fileName[0][-8:-4]
    report_info = [company, report, year]

    #reads file converts contents to lower case, replaces line breaks with spaces so each word is counted regardless of place in text & capitalization
    company_report = open(report_file, 'r')
    text = company_report.read().lower()
    company_report.close()
    text = re.sub(r'\n', ' ', text).strip()

    #breaks text up by each space and creates list of each text item
    text_items = text.split()

    #counts total amount of text items if they're not numbers (total word count)
    file_total = len([item for item in text_items if not item.isdigit()])

    word_hits = []
    #initializes a dictionary with each Planetary Boundary category as the key
    category_count = {category: 0 for category in interest_words.keys()}
    # initializes category map for locations of each word in the categories
    category_map = {}

    #iterates through each word and category in the word list
    for key, items in interest_words.items():
        #iterates through each word in the word list
        for hit in items:
            if '*' in hit and '>' not in hit:
                # terms are marked with '*' if we want to search for different prefixes and suffixes
                # terms are marked with '>' if they contain multiple words, this code segment only applies to single-word terms
                root = re.escape(hit[:-1]) # removes '*' marker
                pattern = rf'\b\w*{root}\w*\b' # assigns regex pattern to accept words with different beginning and endings

            elif '>' in hit:
                terms = hit.split(' ') #creates a list of the words in a multi-word term
                patterns = [] #creates list of patterns specific to each word in the term
                for term in terms:
                    if '>' in term:
                        position_pattern = re.escape(term[1:]) # removes '>' marker
                    elif '*' in term:
                        root = re.escape(term[:-1]) # removes '*' marker
                        position_pattern = rf'\b\w*{root}\w*\b' #assigns regex pattern to accept word in the term that could have different prefixes & suffixes
                    else:
                        position_pattern = rf'\b{re.escape(term)}\b' # if no marker for the word, will only count exact matches
                    patterns.append(position_pattern)
                if len(patterns) == 2:
                    pattern = rf"{patterns[0]}(?:\W{{0,4}})\s*{patterns[1]}" # regex pattern for 2-word terms, will count as match if the words are within 4 characters of each other to account for spaces/dashes/articles
                elif len(patterns) == 3:
                    pattern = rf"{patterns[0]}(?:\W{{0,4}})\s*{patterns[1]}(?:\W{{0,4}})\s*{patterns[2]}" #regex pattern for 3-word terms will count as match if words are within 4 characters of each other
            else:
                pattern = rf'\b{re.escape(hit)}\b' # if no marker for the term, will only count exact matches
            #prints list of each term that matched with an item in the word list
            #found = re.findall(pattern,text)
            #print(f'{len(found)}: {found}')

            #creates iterable list with matches found in the text from the regex patterns
            finds = re.finditer(pattern, text)

            # for each match, appends the original item from the wordlist, the word that matched it in the text, and the start and end index of it in the text
            for find in finds:
                word_hits.append([hit, find.group(), find.span()])
                category_count[key] += 1 #updates category count
                category_map[find.group()] = key #updates category map
    double = []
    word_hits.sort(key=lambda x: x[2][0]) # sorts matches by their location in the text
    counted = []

    #iterates through the matches, noting the match that occured before and after them
    for i in range(len(word_hits) - 1):
        prev_word, _, _ = word_hits[i-1]
        curr_word, _, _ = word_hits[i]
        next_word, _, _ = word_hits[i + 1]

        #iterates through the dictionary of one word terms that are also present in multiple word terms
        for part, fulls in partials.items():
            # if the current match in the iteration is a multiple word term and the match before or after it is a corresponding single word term, appends it to a list of double-counts
            if curr_word in fulls:
                if next_word == part:
                    double.append(word_hits[i+1])
                elif prev_word == part:
                    double.append(word_hits[i-1])

        # iterates through the dictionary of terms that are also present in acronyms
        for acronym_part, acronym in acronyms.items():
           # if the current match in the iteration is an acronym and the match before or after it is a corresponding term, appends it to a list of double-counts
           if curr_word in acronym and curr_word not in counted:
               if next_word == acronym_part:
                   double.append(word_hits[i + 1])
               elif prev_word == acronym_part:
                   double.append(word_hits[i - 1])

    #iterates through list of double-counted terms
    for nonCount in double:
        if nonCount in word_hits:
            word_hits.remove(nonCount) # if the term is still in the matched word list, removes it
            # updates category count and map
            category = category_map.get(nonCount[0])
            if category and category_count[category] > 0:
                category_count[category] -= 1
    #print(f'Double Counted: {double}')

    #calculates frequency of terms for each category
    category_frequency = {category: (count / file_total * 100) for category, count in category_count.items()}

    #prints tables of total word match counts and for each category
    print(f'\n{'Total':^50}\n\n{"Word Count":<20}{"Hit Count":<15}{"Frequency (%)":<15}\n{'-' * 50}')
    print(f'{file_total:<20}{len(word_hits):<15}{(len(word_hits) / file_total) * 100:<15.4f}\n')

    print(f'\n{'By Category':^50}\n\n{"Name":<35}{"Hit Count":<15}{"Frequency (%)":<15}\n{'-' * 65}')
    for category in interest_words.keys():
        print(f'{category:<35}{category_count[category]:<15}{category_frequency[category]:<15.4f}')
    return report_info, category_frequency, file_total, len(word_hits)

graph_info = []
csv_info = []
#dictionary of single word terms that are also present in multi-word terms
partials = {'sustainab*': ['sustainable material*'], 'nutrient*': ['>nutrient loading'], 'waste': ['>waste water', '>zero waste'], 'charger*': ['>super charger*']}
#dictionary of terms that could be used to define acronyms
acronyms = {'greenhouse': ['ghg'], 'climat*': ['unfccc', 'ipcc', 'ogci'], '>carbon capture': ['ccs', 'ccus'], 'fluorocarbon*': ['hfc', 'cfc']}



#iterates through each file in a given category and runs the word count function on it
for report in os.listdir('/Users/sophiebell/PycharmProjects/corporate_sustainability/sec_files/utilities'):
    file_path = os.path.join('/Users/sophiebell/PycharmProjects/corporate_sustainability/sec_files/utilities', report)
#file_path = ('/Users/sophiebell/PycharmProjects/corporate_sustainability/sec_files/utilities/AEP2019file_4')
    result = process_file(file_path) # result is the report info [company, report, year], category frequency, file word count, total hits for file

    graph_result = [result[0][0], result[0][1], result[0][2], result[1]] #information needed for frequency graph
    csv_result = graph_result + [result[2], result[3]] #information needed for csv
    graph_info.append(graph_result) #compiles info for graph of all files in sector
    csv_info.append(csv_result) #compiles info for csv for all files in sector

# creates graph
graph_info.sort(key=lambda x: x[2])

company_data = defaultdict(list)
for company, report, year, freq in graph_info:
    company_data[company].append((int(year), freq))

for company in company_data:
    company_data[company].sort(key=lambda x: x[0])

categories = list(graph_info[0][3].keys())
category_colors = plt.cm.tab10.colors

fig, ax = plt.subplots(figsize=(12, 6))

bar_width = 0.2
bar_gap = .005
company_spacing = 1.0
bars_per_company = max(len(v) for v in company_data.values())
total_companies = len(company_data)
x_positions = []
tick_positions = []
tick_labels = []

company_names = list(company_data.keys())
bar_index = 0

for c_idx, company in enumerate(company_names):
    year_data = company_data[company]
    group_start = c_idx * (bars_per_company * (bar_width + bar_gap) + company_spacing)
    for y_idx, (year, freq) in enumerate(year_data):
        x = group_start + y_idx * (bar_width + bar_gap)
        x_positions.append(x)

        bottom = 0
        for cat_idx, category in enumerate(categories):
            height = freq.get(category, 0)
            ax.bar(x, height, bottom=bottom, width=bar_width,
                   color=category_colors[cat_idx % len(category_colors)])
            bottom += height

    mid_x = group_start + ((len(year_data) - 1) * bar_width) / 2
    tick_positions.append(mid_x)
    tick_labels.append(company)

ax.set_xticks(tick_positions)
ax.set_xticklabels(tick_labels)
ax.set_xlabel("Company")
ax.set_ylabel("Frequency (%)")
ax.set_title("Climate Word Frequency by Category")
ax.legend(categories, title="Categories", bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
plt.show()

#creates csv
categories = list(graph_info[0][3].keys())
csv_path = '/Users/sophiebell/PycharmProjects/corporate_sustainability/csv_files'
csv_file = os.path.join(csv_path, 'utilities.csv')
csv_headers = ['Company', 'Report', 'Year', 'Total Word Count'] + categories + ['Total Hit Count', 'Total Frequency']
csv_rows = []

for company, report, year, category_dict, Wcount, Hcount in csv_info:
    row = [company, report, year, Wcount]
    for category in categories:
        row.append(category_dict.get(category, 0))

    total_freq = Hcount / Wcount if Wcount > 0 else 0
    row.extend([Hcount, total_freq])

    csv_rows.append(row)

with open(csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(csv_headers)
    writer.writerows(csv_rows)


