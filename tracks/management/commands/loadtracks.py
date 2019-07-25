from django.core.management.base import BaseCommand, CommandError
from tracks.models import Genome, Track, TFName, CellType, RepName
import yaml


def read_tracks_from_config(filename):
    tracks = []
    with open(filename) as infile:
        data = yaml.safe_load(infile)
        for genome in data:
            for track_data in genome['tracks']:
                track_dict = track_data.copy()
                track_dict['genome_name'] = genome['assembly']
                tracks.append(track_dict)
    return tracks


class Command(BaseCommand):
    help = 'Loads data into the database'

    def add_arguments(self, parser):
        parser.add_argument('filename')

    def handle(self, *args, **options):
        filename = options['filename']
        for track_dict in read_tracks_from_config(filename):
            genome_name = track_dict['genome_name']
            genome, _ = Genome.objects.get_or_create(name=genome_name)
            tf_name, _ = TFName.objects.get_or_create(name=track_dict['tf_name'])
            cell_type, _ = CellType.objects.get_or_create(name=track_dict['cell_type'])
            rep_name, _ = RepName.objects.get_or_create(name=track_dict['rep_name'])
            Track.objects.create(
                genome=genome,
                name=track_dict['track'],
                file_type=track_dict['type'],
                short_label=track_dict['shortLabel'],
                long_label=track_dict['longLabel'],
                big_data_url=track_dict['bigDataUrl'],
                tf_name=tf_name,
                cell_type=cell_type,
                rep_name=rep_name,
            )
