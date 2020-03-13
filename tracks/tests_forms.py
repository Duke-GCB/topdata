from django.test import TestCase
from django.core.exceptions import ValidationError
from tracks.forms import BootstrapErrorList, TranscriptionFactorForm, FormFields, CellTypeForm, \
    TracksMultipleChoiceField, TracksForm
from tracks.models import TranscriptionFactor, CellType, Genome, RepName, Track
from unittest.mock import patch, Mock


class TestCaseWithTrackData(TestCase):
    def setUp(self):
        genome = Genome.objects.create(name='hg19')
        tf1 = TranscriptionFactor.objects.create(name='AR')
        tf2 = TranscriptionFactor.objects.create(name='ATF')
        cell_type1 = CellType.objects.create(name='8988T')
        cell_type2 = CellType.objects.create(name='CLL')
        rep1 = RepName.objects.create(name='rep1')

        for tf in [tf1, tf2]:
            for ct in [cell_type1, cell_type2]:
                for rep in [rep1]:
                    name = '{}{}{}'.format(tf.name, ct.name, rep.name)
                    Track.objects.create(
                        genome=genome,
                        name=name,
                        short_label=name,
                        long_label=name,
                        big_data_url='https://github.com/Duke-GCB/topdata',
                        file_type='bigWig',
                        tf=tf,
                        cell_type=ct,
                        rep_name=rep,
                        position='chr1:100-200'
                    )


class BootstrapErrorListTest(TestCase):
    def test_as_ul(self):
        error_list = BootstrapErrorList()
        error_list.data = ['bad count']
        expected = '<ul class="errorlist alert alert-warning"><li class="d-block">bad count</li></ul>'
        self.assertEqual(error_list.as_ul(), expected)


class TranscriptionFactorFormTest(TestCase):
    def setUp(self):
        TranscriptionFactor.objects.create(name='AR')
        TranscriptionFactor.objects.create(name='ATF')

    def test_initial_empty(self):
        form = TranscriptionFactorForm()
        self.assertEqual(form.is_valid(), False)
        self.assertEqual(form.errors, {})
        paragraph_html = form.as_p()
        self.assertIn('<option value="AR">AR</option>', paragraph_html)
        self.assertIn('<option value="ATF">ATF</option>', paragraph_html)

    def test_data_empty(self):
        form = TranscriptionFactorForm(data={FormFields.TF_NAME: []})
        self.assertEqual(form.is_valid(), False)
        self.assertEqual(form.errors, {FormFields.TF_NAME: ['This field is required.']})
        paragraph_html = form.as_p()
        self.assertIn('<option value="AR">AR</option>', paragraph_html)
        self.assertIn('<option value="ATF">ATF</option>', paragraph_html)

    def test_data_valid(self):
        form = TranscriptionFactorForm(data={FormFields.TF_NAME: ['AR']})
        self.assertEqual(form.is_valid(), True)
        self.assertEqual(form.errors, {})
        paragraph_html = form.as_p()
        self.assertIn('<option value="AR" selected>AR</option>', paragraph_html)
        self.assertIn('<option value="ATF">ATF</option>', paragraph_html)

    def test_next_step_url(self):
        form = TranscriptionFactorForm(data={FormFields.TF_NAME: ['AR', 'ATF']})
        form.is_valid()
        self.assertEqual(form.next_step_url(), '/tracks/select-cell-type/?tf=AR&tf=ATF')


class CellTypeFormTest(TestCaseWithTrackData):
    def test_initial_empty(self):
        form = CellTypeForm(initial={FormFields.TF_NAME: ['AR']})
        self.assertEqual(form.is_valid(), False)
        self.assertEqual(form.errors, {})
        paragraph_html = form.as_p()
        self.assertIn('<option value="8988T">8988T</option>', paragraph_html)
        self.assertIn('<option value="CLL">CLL</option>', paragraph_html)
        # hidden selected AR tf should be in the form
        self.assertIn('<input type="hidden" name="tf" value="AR"', paragraph_html)

    def test_data_empty(self):
        form = CellTypeForm(data={FormFields.TF_NAME: ['AR'], FormFields.CELL_TYPE: []})
        self.assertEqual(form.is_valid(), False)
        self.assertEqual(form.errors, {FormFields.CELL_TYPE: ['This field is required.']})
        paragraph_html = form.as_p()
        self.assertIn('<option value="8988T">8988T</option>', paragraph_html)
        self.assertIn('<option value="CLL">CLL</option>', paragraph_html)
        # hidden selected AR tf should be in the form
        self.assertIn('<input type="hidden" name="tf" value="AR"', paragraph_html)

    def test_data_valid(self):
        form = CellTypeForm(data={FormFields.TF_NAME: ['AR'], FormFields.CELL_TYPE: ['CLL']})
        self.assertEqual(form.is_valid(), True)
        self.assertEqual(form.errors, {})
        paragraph_html = form.as_p()
        self.assertIn('<option value="8988T">8988T</option>', paragraph_html)
        self.assertIn('<option value="CLL" selected>CLL</option>', paragraph_html)
        # hidden selected AR tf should be in the form
        self.assertIn('<input type="hidden" name="tf" value="AR"', paragraph_html)

    @patch('tracks.forms.settings')
    def test_too_many_tracks(self, mock_settings):
        mock_settings.TRACK_SELECTION_LIMIT = 3
        form = CellTypeForm(data={FormFields.TF_NAME: ['AR', 'ATF'], FormFields.CELL_TYPE: ['8988T', 'CLL']})
        self.assertEqual(form.is_valid(), False)
        self.assertEqual(form.errors, {
            '__all__': ['Too many cell types selected. Your selection resulted in 4 tracks. Max allowed is 3.']
        })

        mock_settings.TRACK_SELECTION_LIMIT = 100
        form = CellTypeForm(data={FormFields.TF_NAME: ['AR', 'ATF'], FormFields.CELL_TYPE: ['8988T', 'CLL']})
        self.assertEqual(form.is_valid(), True)
        self.assertEqual(form.errors, {})

    def test_next_step_url(self):
        form = CellTypeForm(data={FormFields.TF_NAME: ['AR', 'ATF'], FormFields.CELL_TYPE: ['8988T', 'CLL']})
        form.is_valid()
        self.assertEqual(form.next_step_url(), '/tracks/select-tracks/?tf=AR&tf=ATF&celltype=8988T&celltype=CLL')


class TracksMultipleChoiceFieldTest(TestCaseWithTrackData):
    def test_validate(self):
        field = TracksMultipleChoiceField()
        for valid_value in [['AR,8988T'], ['AR,CLL'], ['ATF,8988T'], ['ATF,CLL'], ['AR,8988T', 'AR,CLL']]:
            field.validate(value=valid_value)
        for bad_value in [['8988T,AR'], ['CLL,ATF'], ['invalid'], ['AR,8988T', 'invalid']]:
            with self.assertRaises(ValidationError) as raised_exception:
                field.validate(value=bad_value)
            self.assertEqual(raised_exception.exception.code, 'invalid_choice')


class TracksFormTest(TestCaseWithTrackData):
    def test_initial_empty(self):
        form = TracksForm()
        self.assertEqual(form.is_valid(), False)
        self.assertEqual(form.errors, {})

    def test_data_empty(self):
        form = TracksForm(data={'track_str': []})
        self.assertEqual(form.is_valid(), False)
        self.assertEqual(form.errors, {'track_str': ['This field is required.']})

    def test_data_invalid(self):
        form = TracksForm(data={'track_str': ['X,Y']})
        self.assertEqual(form.is_valid(), False)
        self.assertEqual(form.errors, {'track_str': ['Select a valid choice. X,Y is not one of the available choices.']})

    def test_data_valid(self):
        form = TracksForm(data={'track_str': ['AR,8988T']})
        self.assertEqual(form.is_valid(), True)
        self.assertEqual(form.errors, {})

    def test_next_step_url(self):
        mock_request = Mock()
        mock_request.build_absolute_uri = lambda x: x
        form = TracksForm(data={'track_str': ['AR,8988T', 'AR,CLL', 'ATF,CLL']})
        form.is_valid()
        url = form.next_step_url(mock_request)
        self.assertEqual(url, 'https://genome.ucsc.edu/cgi-bin/hgTracks?org=human&db=hg19&hubUrl=/tracks/1_2_4/hub.txt&position=chr1:100-200')
