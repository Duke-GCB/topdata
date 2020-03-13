from django.test import TestCase, Client
from django.urls import reverse
from tracks.views import Navigation, Steps
from tracks.forms import TranscriptionFactorForm, CellTypeForm, FormFields
from unittest.mock import patch
from tracks.models import Genome, TranscriptionFactor, CellType, RepName, Track

STATUS_OK = 200
STATUS_FOUND = 302


class NavigationTests(TestCase):
    def test_make_items_tracks(self):
        items = Navigation.make_items(Navigation.TRACKS_PAGE)
        self.assertEqual(items, [
            {'label': 'Tracks', 'url_name': 'tracks-select_factors', 'is_active': True},
            {'label': 'About', 'url_name': 'tracks-about', 'is_active': False}
        ])

    def test_make_items_about(self):
        items = Navigation.make_items(Navigation.ABOUT_PAGE)
        self.assertEqual(items, [
            {'label': 'Tracks', 'url_name': 'tracks-select_factors', 'is_active': False},
            {'label': 'About', 'url_name': 'tracks-about', 'is_active': True}
        ])

    @patch('tracks.views.settings')
    def test_make_template_context(self, mock_settings):
        mock_settings.ALL_DATA_URL = 'someurl'
        context = Navigation.make_template_context(Navigation.TRACKS_PAGE, base_context={"count": 1})
        self.assertEqual(context, {
            'count': 1,
            'nav_title': 'Top Data',
            'nav_items': [
                {'label': 'Tracks', 'url_name': 'tracks-select_factors', 'is_active': True},
                {'label': 'About', 'url_name': 'tracks-about', 'is_active': False}
            ], 'nav_download_all_url': 'someurl'
        })


class StepsTests(TestCase):
    def test_make_items_tfs(self):
        items = Steps.make_items(Steps.TRANSCRIPTION_FACTORS)
        self.assertEqual(items, [
            {'label': Steps.TRANSCRIPTION_FACTORS, 'is_active': True}
        ])

    def test_make_items_cell_type(self):
        items = Steps.make_items(Steps.CELL_TYPES)
        self.assertEqual(items, [
            {'label': Steps.TRANSCRIPTION_FACTORS, 'is_active': False},
            {'label': Steps.CELL_TYPES, 'is_active': True}
        ])

    def test_make_items_tracks(self):
        items = Steps.make_items(Steps.TRACKS)
        self.assertEqual(items, [
            {'label': Steps.TRANSCRIPTION_FACTORS, 'is_active': False},
            {'label': Steps.CELL_TYPES, 'is_active': False},
            {'label': Steps.TRACKS, 'is_active': True}
        ])


class ViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.genome = Genome.objects.create(name='hg19')
        self.tf1 = TranscriptionFactor.objects.create(name='AR')
        self.tf2 = TranscriptionFactor.objects.create(name='ATF')
        cell_type1 = CellType.objects.create(name='8988T')
        cell_type2 = CellType.objects.create(name='CLL')
        rep1 = RepName.objects.create(name='rep1')

        for tf in [self.tf1, self.tf2]:
            for ct in [cell_type1, cell_type2]:
                for rep in [rep1]:
                    name = '{}{}{}'.format(tf.name, ct.name, rep.name)
                    Track.objects.create(
                        genome=self.genome,
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

    def test_tracks_index_redirects_to_select_factors(self):
        resp = self.client.get(reverse('tracks-index'))
        self.assertEqual(resp.status_code, STATUS_FOUND)
        self.assertEqual(resp.url, '/tracks/select-factors/')

    def test_tracks_about(self):
        resp = self.client.get(reverse('tracks-about'))
        self.assertEqual(resp.status_code, STATUS_OK)

    def _check_nav_context(self, resp):
        self.assertEqual(resp.context['nav_title'], Navigation.TITLE)
        nav_items_urls = [nav_item['url_name'] for nav_item in resp.context['nav_items']]
        self.assertEqual(nav_items_urls, ['tracks-select_factors', 'tracks-about'])

    def test_select_factors_get(self):
        resp = self.client.get(reverse('tracks-select_factors'))
        self.assertEqual(resp.status_code, STATUS_OK)
        self._check_nav_context(resp)
        self.assertEqual(resp.context['step_items'], Steps.make_items(Steps.TRANSCRIPTION_FACTORS))
        self.assertIsInstance(resp.context['form'], TranscriptionFactorForm)
        self.assertEqual(resp.context['form'].errors, {})

    def test_select_factors_post_without_data(self):
        resp = self.client.post(reverse('tracks-select_factors'))
        self.assertEqual(resp.status_code, STATUS_OK)
        self._check_nav_context(resp)
        self.assertEqual(resp.context['step_items'], Steps.make_items(Steps.TRANSCRIPTION_FACTORS))
        self.assertIsInstance(resp.context['form'], TranscriptionFactorForm)
        self.assertEqual(resp.context['form'].errors, {FormFields.TF_NAME: ['This field is required.']})

    def test_select_factors_post_with_data(self):
        resp = self.client.post(reverse('tracks-select_factors'), data={FormFields.TF_NAME: ["AR","ATF"]})
        # when user posts with good data direct them to select cell type
        self.assertEqual(resp.status_code, STATUS_FOUND)
        self.assertEqual(resp.url, reverse('tracks-select_cell_type') + '?tf=AR&tf=ATF')

    def test_select_cell_type_get_without_data(self):
        resp = self.client.get(reverse('tracks-select_cell_type'))
        # if users directly navigate to select cell type without selecting transcription factors
        # go back to select_factors
        self.assertEqual(resp.status_code, STATUS_FOUND)
        self.assertEqual(resp.url, reverse('tracks-select_factors'))

    def test_select_cell_type_get_with_data(self):
        resp = self.client.get(reverse('tracks-select_cell_type') + '?tf=AR&tf=ATF')
        self.assertEqual(resp.status_code, STATUS_OK)
        self._check_nav_context(resp)
        self.assertEqual(resp.context['step_items'], Steps.make_items(Steps.CELL_TYPES))
        resp_form = resp.context['form']
        self.assertIsInstance(resp_form, CellTypeForm)
        self.assertEqual(resp_form.errors, {})
        tf_names = [tf.name for tf in resp_form.cleaned_data[FormFields.TF_NAME]]
        self.assertEqual(tf_names, ['AR', 'ATF'])

    def test_select_cell_type_post_without_data(self):
        resp = self.client.post(reverse('tracks-select_cell_type'))
        self.assertEqual(resp.status_code, STATUS_OK)
        self._check_nav_context(resp)
        self.assertEqual(resp.context['step_items'], Steps.make_items(Steps.CELL_TYPES))
        resp_form = resp.context['form']
        self.assertIsInstance(resp_form, CellTypeForm)
        self.assertEqual(resp_form.errors, {FormFields.CELL_TYPE: ['This field is required.']})

    def test_select_cell_type_post_with_data(self):
        resp = self.client.post(reverse('tracks-select_cell_type'), data={
            FormFields.TF_NAME: ["AR", "ATF"],
            FormFields.CELL_TYPE: ["8988T", "CLL"],
        })
        # when user posts with good data direct them to select tracks
        self.assertEqual(resp.status_code, STATUS_FOUND)
        self.assertEqual(resp.url, reverse('tracks-select_tracks') + '?tf=AR&tf=ATF&celltype=8988T&celltype=CLL')

    def test_select_tracks_get_without_data(self):
        resp = self.client.get(reverse('tracks-select_tracks'))
        # if users directly navigate to select tracks type without selecting transcription factors and cell types
        # go back to select_factors
        self.assertEqual(resp.status_code, STATUS_FOUND)
        self.assertEqual(resp.url, reverse('tracks-select_factors'))

    def test_select_tracks_get_with_data(self):
        resp = self.client.get(reverse('tracks-select_tracks') + '?tf=AR&tf=ATF&celltype=8988T&celltype=CLL')
        self.assertEqual(resp.status_code, STATUS_OK)
        self._check_nav_context(resp)
        self.assertEqual(resp.context['step_items'], Steps.make_items(Steps.TRACKS))
        tf_names = [tf.name for tf in resp.context['tfs']]
        self.assertEqual(tf_names, ['AR','ATF'])
        celltype_names = [celltype.name for celltype in resp.context['celltypes']]
        self.assertEqual(celltype_names, ['8988T','CLL'])

    def test_select_tracks_post_with_data(self):
        resp = self.client.post(reverse('tracks-select_tracks'), data={'track_str': ['AR,8988T', 'AR,CLL']})
        self.assertEqual(resp.status_code, STATUS_FOUND)
        expected_url = 'https://genome.ucsc.edu/cgi-bin/hgTracks?org=human&db=hg19&' \
                       'hubUrl=http://testserver/tracks/1_2/hub.txt&position=chr1:100-200'
        self.assertEqual(resp.url, expected_url)

    def test_tracks_detail(self):
        resp = self.client.get(reverse('tracks-detail', kwargs={'encoded_key_value': '1_2'}))
        self.assertEqual(resp.status_code, STATUS_OK)
        self.assertEqual(resp.context['genomes'], {self.genome})

    def test_tracks_hub(self):
        resp = self.client.get(reverse('tracks-hub', kwargs={'encoded_key_value': '1_2'}))
        self.assertEqual(resp.status_code, STATUS_OK)
        self.assertEqual(resp.content.decode('utf-8'), """
hub TOPhub_1_2
shortLabel TopData
longLabel TopData
genomesFile genomes.txt
email test@test.test
descriptionUrl http://www.genome.duke.edu
""".strip())

    def test_tracks_genomes(self):
        resp = self.client.get(reverse('tracks-genomes', kwargs={'encoded_key_value': '1_2'}))
        self.assertEqual(resp.status_code, STATUS_OK)
        self.assertEqual(resp.content.decode('utf-8'), """
genome hg19
trackDb hg19/trackDb.txt
""".lstrip())

    def test_tracks_trackdb(self):
        resp = self.client.get(reverse('tracks-trackdb', kwargs={'encoded_key_value': '1_2', 'genome': 'hg19'}))
        self.assertEqual(resp.status_code, STATUS_OK)
        self.assertEqual(resp.content.decode('utf-8'), """
track AR8988Trep1
bigDataUrl https://github.com/Duke-GCB/topdata
shortLabel AR8988Trep1
longLabel AR8988Trep1
type bigWig
graphTypeDefault bar
autoScale off
maxHeightPixels 100:32:8
viewLimits 0:100
visibility dense


track ARCLLrep1
bigDataUrl https://github.com/Duke-GCB/topdata
shortLabel ARCLLrep1
longLabel ARCLLrep1
type bigWig
graphTypeDefault bar
autoScale off
maxHeightPixels 100:32:8
viewLimits 0:100
visibility dense

""")

