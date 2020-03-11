from django.test import TestCase
from django.db.utils import IntegrityError
from tracks.models import *

class TracksTests(TestCase):
    def setUp(self):
        self.genome1 = Genome.objects.create(name='hg19')
        self.genome2 = Genome.objects.create(name='hg38')
        self.tf1 = TranscriptionFactor.objects.create(name='tf1')
        self.tf2 = TranscriptionFactor.objects.create(name='tf2')
        self.celltype1 = CellType.objects.create(name='celltype1')
        self.celltype2 = CellType.objects.create(name='celltype2')
        self.rep1 = RepName.objects.create(name='rep1')
        self.rep2 = RepName.objects.create(name='rep2')

    def test_create(self):
        for tf in [self.tf1, self.tf2]:
            for ct in [self.celltype1, self.celltype2]:
                for rep in [self.rep1, self.rep2]:
                    name = '{}{}{}'.format(tf.name, ct.name, rep.name)
                    Track.objects.create(
                        genome=self.genome1,
                        name=name,
                        short_label=name,
                        long_label=name,
                        big_data_url='https://github.com/Duke-GCB/topdata',
                        file_type='bigWig',
                        tf=tf,
                        cell_type=ct,
                        rep_name=rep,
                    )
        self.assertEqual(len(Track.objects.all()), 8)
        self.assertEqual(len(Track.objects.filter(tf=self.tf1)), 4)


    def test_create_same_name_and_same_genome(self):
        name = "myname"
        Track.objects.create(
            genome=self.genome1,
            name=name,
            short_label=name,
            long_label=name,
            big_data_url='https://github.com/Duke-GCB/topdata',
            file_type='bigWig',
            tf=self.tf1,
            cell_type=self.celltype1,
            rep_name=self.rep1,
        )
        with self.assertRaises(IntegrityError):
            Track.objects.create(
                genome=self.genome1,
                name=name,
                short_label=name,
                long_label=name,
                big_data_url='https://github.com/Duke-GCB/topdata',
                file_type='bigWig',
                tf=self.tf2,
                cell_type=self.celltype1,
                rep_name=self.rep1,
            )

    def test_create_same_name_and_diff_genome(self):
        name = "myname"
        Track.objects.create(
            genome=self.genome1,
            name=name,
            short_label=name,
            long_label=name,
            big_data_url='https://github.com/Duke-GCB/topdata',
            file_type='bigWig',
            tf=self.tf1,
            cell_type=self.celltype1,
            rep_name=self.rep1,
        )
        Track.objects.create(
            genome=self.genome2,
            name=name,
            short_label=name,
            long_label=name,
            big_data_url='https://github.com/Duke-GCB/topdata',
            file_type='bigWig',
            tf=self.tf2,
            cell_type=self.celltype1,
            rep_name=self.rep1,
        )
