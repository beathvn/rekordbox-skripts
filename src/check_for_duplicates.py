from argparse import ArgumentParser

import xmltodict
import pandas as pd


def print_divider():
    print('--------------------------')


def load_dataframe_from_xml(filepath):
    # check if the given filepath is a .xml file
    if filepath[-4:] != '.xml':
        raise ValueError(
            f'Please provide a .xml file. You passed a {filepath[-4:]} file.')

    # opening the file
    with open(filepath, 'r') as xml_file:
        input_data = xmltodict.parse(xml_file.read())

    # converting the needed data into a dataframe
    input_data = input_data['DJ_PLAYLISTS']['COLLECTION']['TRACK']
    return pd.DataFrame(input_data)


def check_for_duplicates():
    parser = ArgumentParser()
    parser.add_argument('-p', '--path_to_xml')

    # parsing the passed arguments
    args = parser.parse_args()
    filepath = args.path_to_xml

    if filepath is None:
        raise ValueError(
            'Please provide a valid .xml filepath to your rekordbox database as a program argument!')

    # getting the dataframe
    data = load_dataframe_from_xml(filepath)

    # searching for duplicates
    results = data['@Location'].duplicated()

    # printing the names of the duplicated songs
    duplicate_songnames = []
    for index, result in enumerate(results):
        if result:
            duplicate_songnames.append(data.iloc[index]['@Name'])

    if len(duplicate_songnames) != 0:
        print(
            f'🚨 {len(duplicate_songnames)} TRACKS WHERE FOUND pointing to the same file on your harddisk:')
        print_divider()
        for currsong in duplicate_songnames:
            print('- ' + currsong)
        print_divider()
    else:
        print('✅ No songs appearing more than once were found.')


if __name__ == "__main__":
    check_for_duplicates()
