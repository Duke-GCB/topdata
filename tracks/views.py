from django.http import HttpResponse
from django.template import loader
from django.conf import settings
from django.utils.html import quote
from jinja2 import Template
from django.shortcuts import reverse, redirect, render
from tracks.models import Track, TranscriptionFactor, CellType, Genome
from tracks.forms import TranscriptionFactorForm, CellTypeForm, TracksForm, FormFields
import os


TEMPLATE_CONFIG = 'templates.yaml'
JINJA_TEMPLATE_DIR = 'jinja2'


class Navigation(object):
    TITLE = "Top Data"
    TRACKS_PAGE = 'Tracks'
    ABOUT_PAGE = 'About'

    @staticmethod
    def make_items(active_page):
        return [
            {
                'label': Navigation.TRACKS_PAGE,
                'url_name': 'tracks-select_factors',
                'is_active': active_page == Navigation.TRACKS_PAGE,
            },
            {
                'label': Navigation.ABOUT_PAGE,
                'url_name': 'tracks-about',
                'is_active': active_page == Navigation.ABOUT_PAGE,
            },
        ]

    @staticmethod
    def make_template_context(active_page, base_context={}):
        context = base_context.copy()
        context.update({
            'nav_title': Navigation.TITLE,
            'nav_items': Navigation.make_items(active_page=active_page),
            'nav_download_all_url': settings.ALL_DATA_URL,
        })
        return context


class Steps(object):
    TRANSCRIPTION_FACTORS = 'Transcription Factors'
    CELL_TYPES = 'Cell Type'
    TRACKS = 'Tracks'

    @staticmethod
    def make_items(active_step_name):
        items = []
        for step_name in [Steps.TRANSCRIPTION_FACTORS, Steps.CELL_TYPES, Steps.TRACKS]:
            items.append({
                "label": step_name,
                "is_active": active_step_name == step_name,
            })
            if active_step_name == step_name:
                break
        return items


def index(request):
    return redirect('tracks-select_factors')

def about(request):
    template = loader.get_template('tracks/about.html')
    context = Navigation.make_template_context(Navigation.ABOUT_PAGE)
    return HttpResponse(template.render(context, request))


def select_factors(request):
    if request.method == 'POST':
        form = TranscriptionFactorForm(request.POST)
        if form.is_valid():
            return redirect(form.next_step_url())
    else:
        form = TranscriptionFactorForm()
    template = loader.get_template('tracks/select_factors.html')
    context = Navigation.make_template_context(Navigation.TRACKS_PAGE, {
        'step_items': Steps.make_items(Steps.TRANSCRIPTION_FACTORS),
        'form': form,
    })
    return HttpResponse(template.render(context, request))


def select_cell_type(request):
    if request.method == 'POST':
        form = CellTypeForm(request.POST)
        if form.is_valid():
            return redirect(form.next_step_url())
    else:
        if not request.GET.getlist(FormFields.TF_NAME):
            return redirect('tracks-select_factors')
        form = CellTypeForm(request.GET)
        # clear cell type error so user isn't warned before they have a chance to enter data
        del form.errors[FormFields.CELL_TYPE]
    template = loader.get_template('tracks/select_cell_type.html')
    context = Navigation.make_template_context(Navigation.TRACKS_PAGE, {
        'step_items': Steps.make_items(Steps.CELL_TYPES),
        'form': form
    })
    return HttpResponse(template.render(context, request))


def select_tracks(request):
    if request.method == 'POST':
        form = TracksForm(request.POST)
        if form.is_valid():
            return redirect(form.next_step_url(request))
    tfs_names = request.GET.getlist(FormFields.TF_NAME)
    celltypes_names = request.GET.getlist(FormFields.CELL_TYPE)
    if not tfs_names or not celltypes_names:
        return redirect('tracks-select_factors')
    context = Navigation.make_template_context(Navigation.TRACKS_PAGE, {
        'step_items': Steps.make_items(Steps.TRACKS),
        'tfs': TranscriptionFactor.objects.filter(pk__in=tfs_names),
        'celltypes': CellType.objects.filter(pk__in=celltypes_names),
    })
    return render(request, 'tracks/select_tracks.html', context)


def get_track_ids(tf_cell_type_pairs):
    track_ids = []
    for tf, cell_type in tf_cell_type_pairs:
        for track in Track.objects.filter(tf__name=tf, cell_type__name=cell_type):
            track_ids.append(str(track.id))
    return track_ids


def get_position_from_first_track(tf_cell_type_pairs):
    first_tf, first_cell_type = tf_cell_type_pairs[0]
    track = Track.objects.filter(tf__name=first_tf, cell_type__name=first_cell_type)[0]
    return track.position


def get_tracks(encoded_key_value):
    return Track.objects.filter(pk__in=encoded_key_value.split("_"))


def decode_track_keys(encoded_track_strs):
    track_strs = encoded_track_strs.split("__")
    return [track_str.split("_") for track_str in track_strs]


def detail(request, encoded_key_value):
    genomes = set()
    for track in get_tracks(encoded_key_value):
        genomes.add(track.genome)
    template = loader.get_template('tracks/detail.html')
    context = {
        'genomes': genomes
    }
    return HttpResponse(template.render(context, request))


def get_template(template_filename):
    template_path = os.path.join(JINJA_TEMPLATE_DIR, template_filename)
    with open(template_path) as infile:
        return Template(infile.read())


def hub(request, encoded_key_value):
    template = get_template('hub.txt.j2')
    context = {
        'hub_id': encoded_key_value
    }
    return HttpResponse(template.render(context), content_type='text/plain')

def genomes(request, encoded_key_value):
    genomes = set()
    for track in get_tracks(encoded_key_value):
        genomes.add(track.genome)
    template = get_template('genomes.txt.j2')
    context = {
        'genomes': genomes,
    }
    return HttpResponse(template.render(context), content_type='text/plain')

def track_db(request, encoded_key_value, genome):
    tracks = get_tracks(encoded_key_value).filter(genome__name=genome)
    template = get_template('trackDb.txt.j2')
    context = {
        'tracks': tracks
    }
    return HttpResponse(template.render(context), content_type='text/plain')
