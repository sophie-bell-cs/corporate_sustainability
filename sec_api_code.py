'''
Corporate Sustainability Analysis
This code uses the FullTextSearch and PdfGenerator Api from Edgar to access user specified files from the SEC.
It then converts them from their original format (xml or similar) to a PDF, which can then be read and written into a text file.
The file is added to a user specified category, and can then be read by the processFile.py code.
'''
#packages used in code
import pandas as pd
from sec_api import FullTextSearchApi
from sec_api import PdfGeneratorApi
import os
import PyPDF2
import json

#convert nested json data from SEC website to csv, then dictionary
cik_ticker_name_file = open('/Users/sophiebell/PycharmProjects/corporate_sustainability/cik_ticker_name.json', 'r')
cik_ticker_name_data = json.load(cik_ticker_name_file)
cik_ticker_name = pd.DataFrame.from_dict(cik_ticker_name_data, orient='index')
cik_ticker_name.rename(columns={'cik_str': 'CIK', 'ticker': 'Ticker', 'title': 'Company Name'}, inplace=True)
cik_ticker_name.to_csv('companies.csv', index=False)
company_dict = {}
company_data = open('companies.csv', 'r')
companies = company_data.readlines()
for company in companies[1:]:
    infos = company.split(',')
    company_dict[infos[1]] = [infos[2].strip('\n'), infos[0]]
ticker_list = list(company_dict.keys())

if __name__ == "__sec_api_code__":
    #user choices for search query
    company_search_input = input('Enter the tickers of the companies of interest, separated by commas (aapl,nvda): ')
    company_search = company_search_input.split(',')
    ciks = []
    for c in company_search:
        ticker = c.upper().strip()
        cik = str(company_dict[ticker][1])
        ciks.append(cik)
        print(f"Company Name: {company_dict[ticker][0]}\nCIK Number: {cik}")
        print()

    date_search_input = input('Enter start then end date of search, separated by commas (YYYY-MM-DD,YYYY-MM-DD): ')
    date_search = date_search_input.split(',')
    start = str(date_search[0])
    end = str(date_search[1])
    categ = input('Category: ')
    directory = f'/Users/sophiebell/PycharmProjects/corporate_sustainability/sec_files/{categ.lower()}'


    #api key for id
    api_key = '45d4ca099a4411323d51f5312cd549be91f82add5a013df58cc2abcff97bd318'
    fullTextSearchApi = FullTextSearchApi(api_key)
    pdfGeneratorApi = PdfGeneratorApi(api_key)

    #based on user input, used to search api
    search_parameters = {
        'query': ' ',
        'ciks': ciks,
        'formTypes': ["10-K"],
        'startDate': start,
        'endDate': end,
    }

    files = [categ.lower()]

    #creates dataframe of filings that match the search parameters
    response = fullTextSearchApi.get_filings(search_parameters)
    filings_json = response['filings']
    filings_df = pd.DataFrame(filings_json)
    filings_df.head()
    print(filings_df)

    #creates a list of the url, company ticker, form, and date of each filing that matched the search
    info_for_dl = []
    for _, row in filings_df.iterrows():
        info_for_dl.append([row['filingUrl'], row['ticker'], row['type'], row['filedAt']])
    info_for_dl.sort(key=lambda x: x[1])

    indexer = 0
    for entry in info_for_dl:
        url, form_name= entry[0], entry[2]
        file_content = pdfGeneratorApi.get_pdf(url)
        if form_name == '10-K':
            company, year = entry[1], entry[3][:4]
            Lfile = f'{company}{year}file_{indexer}'
            file_name = os.path.join(directory, Lfile)
            with open(file_name, 'wb') as pdf_file:
                pdf_file.write(file_content)
                print(f'{Lfile} created.')
        elif form_name == '10-K/A':
            documenting = f'file_{indexer-1}'
            with open(file_name, 'ab') as pdf_file:
                pdf_file.write(file_content)
                print(f'{documenting} amended.')
        indexer += 1

    for pdf in os.listdir(directory):
        file = os.path.join(directory, pdf)
        text = ''
        with open(file, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + '\n'
        txt_file_name = file.replace('.pdf', '.txt')
        with open(txt_file_name, 'w') as txt_file:
            txt_file.write(text)
            files.append(txt_file_name)
            print(f'{pdf} ready to parse.')


