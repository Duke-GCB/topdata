from django.test import TestCase
from tracks.management.commands.loadtracks import Command
from tracks.models import *
from unittest.mock import patch, mock_open

EXAMPLE_TRACKS_YAML = """
- assembly: hg19
  tracks:
  - bigDataUrl: https://github.com/Duke-GCB/topdata/fakedata/AR_8988T_rep1.bw
    cell_type: 8988T
    longLabel: AR 8988T rep1
    rep_name: rep1
    shortLabel: AR 8988T rep1
    tf_name: AR
    track: AR_8988T_rep1
    type: bigWig
    position: "chr1:35000-40000"
  - bigDataUrl: https://github.com/Duke-GCB/topdata/fakedata/AR_8988T_rep2.bw
    cell_type: 8988T
    longLabel: AR 8988T rep2
    rep_name: rep2
    shortLabel: AR 8988T rep2
    tf_name: AR
    track: AR_8988T_rep2
    type: bigWig
    position: "chr1:35000-40000"
  - bigDataUrl: https://github.com/Duke-GCB/topdata/fakedata/ATF_8988T_rep1.bw
    cell_type: 8988T
    longLabel: ATF 8988T rep1
    rep_name: rep1
    shortLabel: ATF 8988T rep1
    tf_name: ATF
    track: ATF_8988T_rep1
    type: bigWig
    position: "chr1:35000-40000"
  - bigDataUrl: https://github.com/Duke-GCB/topdata/fakedata/ATF_8988T_rep2.bw
    cell_type: 8988T
    longLabel: ATF 8988T rep2
    rep_name: rep2
    shortLabel: ATF 8988T rep2
    tf_name: ATF
    track: ATF_8988T_rep2
    type: bigWig
    position: "chr1:35000-40000"
"""

class LoadTracksCommandTest(TestCase):
    def test_load_tracks_into_database(self):
        cmd = Command()
        with patch("builtins.open", mock_open(read_data=EXAMPLE_TRACKS_YAML)):
            cmd.handle(filename='/tmp/data.txt')

        genomes = Genome.objects.all()
        self.assertEqual(len(genomes), 1)
        self.assertEqual(genomes[0].name, 'hg19')

        tfs = TranscriptionFactor.objects.order_by('name')
        self.assertEqual(len(tfs), 2)
        self.assertEqual(tfs[0].name, 'AR')
        self.assertEqual(tfs[1].name, 'ATF')

        celltypes = CellType.objects.order_by('name')
        self.assertEqual(len(celltypes), 1)
        self.assertEqual(celltypes[0].name, '8988T')

        reps = RepName.objects.order_by('name')
        self.assertEqual(len(reps), 2)
        self.assertEqual(reps[0].name, 'rep1')
        self.assertEqual(reps[1].name, 'rep2')

        tracks = Track.objects.order_by('name')
        self.assertEqual(len(tracks), 4)
        self.assertEqual(tracks[0].name, 'AR_8988T_rep1')
        self.assertEqual(tracks[1].name, 'AR_8988T_rep2')
        self.assertEqual(tracks[2].name, 'ATF_8988T_rep1')
        self.assertEqual(tracks[3].name, 'ATF_8988T_rep2')

        for track in tracks:
            self.assertEqual(track.genome.name, 'hg19')
            self.assertEqual(track.file_type, 'bigWig')
            self.assertEqual(track.position, 'chr1:35000-40000')
