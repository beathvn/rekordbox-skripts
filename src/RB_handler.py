from typing import Dict

import xmltodict
from datetime import date


class RB_handler():
    def __init__(self, rb5_input_path: str, rb6_input_path: str, location_of_interest: str, keys_to_update: list) -> None:
        # reading the xml files into a pandas data series
        # NOTE: Columns which are not interesting, are already ignored
        self.rawdata_rb5 = self._get_input_data_from_xml(rb5_input_path)
        self.rawdata_rb6 = self._get_input_data_from_xml(rb6_input_path)

        self.data5 = self.rawdata_rb5['DJ_PLAYLISTS']['COLLECTION']['TRACK']
        self.data6 = self.rawdata_rb6['DJ_PLAYLISTS']['COLLECTION']['TRACK']
        print('Successfully loaded the XML Files from Rekordbox 5 and 6')

        self.location_of_interest = location_of_interest

        # this dict holds as keys the title and as values a list of the things you want to write in the end
        self.output_log = {}

        # the given keys will be updated in rb6 given from 5
        self.keys_to_update = keys_to_update

        # generating the rb5 to rb6 dict
        self._generate_mapping_dict_from_5to6()

        return

    def write_log_message(self):

        # writing the name of the files you changed to output
        curr_date = date.today()

        # TODO: if the log folder doesn't exist, create it
        # open file in write mode
        outfile_path = f'./log/{date.today()} log message.txt'
        with open(outfile_path, 'w') as fp:
            for title in self.output_log:
                # write each item on a new line
                fp.write('\n')
                fp.write("%s\n" % title)
                for item in self.output_log[title]:
                    fp.write("%s\n" % item)
            print('Done')

        return

    def update_rb6_according_to_5(self, number_of_tracks: int = -1) -> None:
        indecies_of_rb5 = list(self.map_from_5_to_6.keys())

        # defining the keys for the output dict
        self.output_log['UPDATED TRACKS'] = []
        self.output_log['SKIPPED TRACKS'] = []
        self.output_log['DELETION INFORMATION'] = []

        if number_of_tracks > 0:
            print(f'Updating {number_of_tracks} tracks...')
            indecies_of_rb5 = indecies_of_rb5[:number_of_tracks]
        else:
            print('Updating all tracks...')

        for curr_rb5_index in indecies_of_rb5:
            self._update_file(
                curr_rb5_index, self.map_from_5_to_6[curr_rb5_index])

        self._update_playlists()

        return

    def _update_playlists(self):
        print('Converting playlists...')

        # in this dict we have as key the trackid of rb5 and value is key of rb6
        trackid_mapping = self._get_trackid_mapping()

        # these variable holds the root folder from rekordbox; we just need 5, since 6 gets deleted anyway
        root_folders_rb5 = self.rawdata_rb5['DJ_PLAYLISTS']['PLAYLISTS']['NODE']['NODE']

        # getting the folders you want to change; assign rb6 the values from rb5
        club_vibes_rb6 = root_folders_rb5[3]['NODE'].copy()
        my_tag_rb6 = root_folders_rb5[4]['NODE'].copy()

        # saving them in a list, so we can then iterate over them
        folders_to_convert = [club_vibes_rb6, my_tag_rb6]

        for curr_folder in folders_to_convert:
            for curr_playlist in curr_folder:
                # check if the playlist is empty
                if curr_playlist['@Entries'] != '0':
                    for curr_song in curr_playlist['TRACK']:
                        try:
                            curr_song['@Key'] = trackid_mapping[curr_song['@Key']]
                        except:
                            print(f'Could not convert song {curr_song}')

        # updating the raw_data of rb6
        root_folders_rb6 = self.rawdata_rb6['DJ_PLAYLISTS']['PLAYLISTS']['NODE']['NODE']
        root_folders_rb6[3]['NODE'] = club_vibes_rb6
        root_folders_rb6[4]['NODE'] = my_tag_rb6

        print('Done')

        return

    def _get_trackid_mapping(self):
        track_id_mapping = {}
        for curr_track_index in self.map_from_5_to_6:
            track_id_mapping[self.data5[curr_track_index]['@TrackID']
                             ] = self.data6[self.map_from_5_to_6[curr_track_index]]['@TrackID']

        return track_id_mapping

    def _update_file(self, index_rb5: int, index_rb6: int) -> None:
        # updating self.data6 accoring to self.data5
        correct_data = self.data5[index_rb5]
        data_to_update = self.data6[index_rb6]

        # this bools checks if the metadata was changed, or if it was already correct
        did_change = False

        # going threw the keys you want to change
        for curr_key in self.keys_to_update:
            if curr_key in correct_data.keys():
                # check if the key is available in rb6
                if curr_key in data_to_update.keys():
                    if data_to_update[curr_key] != correct_data[curr_key]:
                        data_to_update[curr_key] = correct_data[curr_key]
                        did_change = True
                else:
                    did_change = True
                    data_to_update[curr_key] = correct_data[curr_key]

            else:
                # if there are information in rb6, which are not available in rb5, just delete those
                if curr_key in data_to_update.keys():
                    trackname = data_to_update['@Name']
                    self.output_log['DELETION INFORMATION'].append(
                        f'Deleted the {curr_key} information in {trackname}')
                    del data_to_update[curr_key]

        # writing in the output message, the name of the track, which was updated
        if did_change:
            self.output_log['UPDATED TRACKS'].append(
                data_to_update['@Name'])
        else:
            self.output_log['SKIPPED TRACKS'].append(
                data_to_update['@Name'])

        return

    def _generate_mapping_dict_from_5to6(self) -> None:
        rb5_index_to_location_dict = self._get_index_location_dict(
            self.data5)
        rb6_index_to_location_dict = self._get_index_location_dict(
            self.data6)

        map_from_5_to_6 = {}
        failed = []
        for curr_key_5 in rb5_index_to_location_dict:
            try:
                map_from_5_to_6[curr_key_5] = list(rb6_index_to_location_dict.keys())[list(
                    rb6_index_to_location_dict.values()).index(rb5_index_to_location_dict[curr_key_5])]
            except:
                failed.append(curr_key_5)
        self.map_from_5_to_6 = map_from_5_to_6

        # writing the files that couldn't be matched
        self.output_log['FILES THAT COULD NOT BE MATCHED FROM 5 TO 6:'] = []
        for failed_index in failed:
            self.output_log['FILES THAT COULD NOT BE MATCHED FROM 5 TO 6:'].append(
                rb5_index_to_location_dict[failed_index])

        print("Successfully created the mapping dict from rb5 to rb6")

        return

    def _get_index_location_dict(self, data) -> Dict:
        # finding all the songs, which are interesting-> the ones in the location starting_string
        interesting_indecies = []
        notinterested_indecies = []

        for index, currTrack in enumerate(data):
            if currTrack['@Location'].startswith(self.location_of_interest):
                interesting_indecies.append(index)
            else:
                notinterested_indecies.append(index)

        # make sure it has the key @Location
        mapped_dict = {}
        for curr_index in interesting_indecies:
            mapped_dict[curr_index] = data[curr_index]['@Location']

        for i in notinterested_indecies:
            print(
                f"Failed to map {data[i]['@Name' ]}".ljust(60) + f"in locatoin: {data[i]['@Location']}")

        return mapped_dict

    def _get_input_data_from_xml(self, filepath: str) -> Dict:
        with open(filepath, 'r') as xml_file:
            input_data = xmltodict.parse(xml_file.read())
            return input_data

    def export_data_to_xml(self, out_path: str) -> None:
        print('Exporting to XML...')
        with open(out_path, 'w') as xml_outfile:
            xml_outfile.write(xmltodict.unparse(self.rawdata_rb6))

        print('Done')

        return
