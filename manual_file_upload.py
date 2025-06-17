"""
Corporate Sustainability Analysis
This code allows users to upload files manually from files on their computer.
"""

import os
import PyPDF2
import difflib
from sec_api_code import company_dict


def find_ticker(input_company):
    #cleans input to ensure closer match to company name
    input = input_company.strip().lower().replace('.', '').replace(',', '')
    if input.upper() in company_dict: #if ticker is input, will return ticker in uppercase
        return input.upper()
    if input in name_to_ticker: #if exact company name is input, will find ticker
        return name_to_ticker[input]
    #if input resembles a company name, will determine what company matches the input and return the ticker of the matched company
    matches = difflib.get_close_matches(input, name_to_ticker.keys(), n=1, cutoff = .6)
    if matches:
        return name_to_ticker[matches[0]]
    return None

for report in os.listdir('/Users/sophiebell/PycharmProjects/corporate_sustainability/manualUpload_pdf'):
    pdf_path = os.path.join('/Users/sophiebell/PycharmProjects/corporate_sustainability/manualUpload_pdf', report)
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""

    print(report)
    company_name = input('What company is this for? (ticker or name): ')
    #uses the already built company_dict with company name and ticker data and enables reverse searching to find ticker via company name
    name_to_ticker = {v[0].lower(): k for k, v in company_dict.items()}
    company = find_ticker(company_name)
    category = input('What category is this from?: ')
    year = input('What year is this report from?: ')

    text_path = os.path.join(f"/Users/sophiebell/PycharmProjects/corporate_sustainability/sec_files/{category.lower()}", f'{company}{year}_companyReport')
    with open(text_path + ".txt", "w") as f:
        f.write(text)