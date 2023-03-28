from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
pd.options.mode.chained_assignment = None

# header
header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36"}

# request url

url = "https://www.domstol.dk/svendborg/retslister/2023/3/civilesager-uge-12/"
r = requests.get(url, headers=header)

columns_and_regex = {
    'title': "(Borgerlig sag).*",
    'ignore': "((Opmærksomheden henledes på).*|^(Mandag|Tirsdag|Onsdag|Torsdag|Fredag|Lørdag|Søndag)$)",
    'empty_line': "(^$)",
    'dato_and_lokale': "\d\d-\d\d-\d\d\d\d kl\.\d\d:\d\d - \d\d:\d\d\..*",
    'Rettens j.nr.': 'Rettens j.nr.:.*',
    'involverede': '(Sagsøgers advokat|Sagsøgtes advokat|Klagers advokat|Sagsøgte|Sagsøger|Sagens persons advokat):.*',
    'dommer': '(Dommer):.*',
    'offentlighed': '(Retsmødet er offentligt)|(Retsmødet er ikke offentligt).*',
    'Sagen drejer sig om': 'Sagen drejer sig om:.*',
}

columns = [
    "title",
    "dato_and_lokale",
    "Rettens j.nr.",
    "involverede",
    "dommer",
    "offentlighed",
    "Sagen drejer sig om",
    "lokale",
    "start_date_time",
]


def get_matching_column(raw_line):
    # Locate the first matching column in columns_and_regex and return the column title
    for key in columns_and_regex:
        regex = columns_and_regex[key]
        # Look for a match against the regex
        found_match = re.match(regex, raw_line)
        if found_match:
            # The column name is the value of key
            return key
        else:
            # Go to next key
            continue

    # No match. Returning false
    return False


# HTML parser = Lister med overblik over URL
soup = BeautifulSoup(r.content, "html.parser")
p_tags = soup.find("div", class_='editor-content').find_all('p')


def parse_p_tag(p_tag):
    removeStrong = re.sub('<strong>|</strong>', '', str(p_tag))
    lines = [_ for _ in removeStrong.split('<br/>')]
    to_return = {"lokale": "", "start_date_time": ""}
    for key in columns_and_regex:
        to_return[key] = ""

    to_return.pop("ignore")
    to_return.pop("empty_line")

    for i in range(len(lines)):
        row = lines[i]

        # Strip row
        row = re.sub('<p(.{0,}?)>|</p>', '', row)
        row = str(row).replace('\\xa0', '').strip()

        matching_column = get_matching_column(row)

        use_append = False

        if matching_column == "dato_and_lokale":
            # Dato og lokale
            # Split dato og lokale
            dato_and_lokale = row.split(". ")
            # Row bliver til dato
            date_and_time = ''
            start_date_time = ''
            end_date_time = ''

            lokale = ''
            if len(dato_and_lokale) == 2:
                lokale = dato_and_lokale[1]
                date_and_time = dato_and_lokale[0].split(" ", 1)
                date_and_time_split = dato_and_lokale[0].split(" - ")
                date_and_time_without_interval = date_and_time_split[0]
                start_date_time = datetime.strptime(
                    date_and_time_split[0], '%d-%m-%Y kl.%H:%M')
                end_date_time = datetime.strptime(
                    date_and_time_split[1], '%H:%M')
                end_date_time = end_date_time.replace(
                    year=start_date_time.year, month=start_date_time.month, day=start_date_time.day)
                row = end_date_time
            to_return["lokale"] = lokale
            to_return["start_date_time"] = start_date_time

        elif matching_column == "Rettens j.nr.":
            # Rettens j.nr.
            row = row.replace('Rettens j.nr.: ', '')
        elif matching_column == "Sagen drejer sig om":
            # Sagen drejer sig om
            row = row.replace('Sagen drejer sig om:', '')
        elif matching_column == "involverede":
            use_append = True

        if use_append:
            to_return[matching_column] += row + ";"
        else:
            to_return[matching_column] = row

    # Convert to_return back to an array

    to_return_as_list = []
    for column_name in columns:
        print(column_name)
        value = to_return[column_name]
        print(value)
        to_return_as_list.append(value)
    return to_return_as_list


# print(parse_p_tag(p_tags[0]))

list_of_lists = []
for i in range(len(p_tags) - 1):
    p = parse_p_tag(p_tags[i])
    # print(p)

    list_of_lists.append(p)

print(list_of_lists)
data_frame = pd.DataFrame(list_of_lists)


# adding column name to the respective columns
data_frame.columns = columns
pd.set_option('display.max_columns', None)