from django.http import HttpResponse
from django.template import loader
from django.db.models import Q
from jinja2 import Template
from django.shortcuts import reverse, redirect, render
from tracks.models import Track, TranscriptionFactor, CellType, Genome
from tracks.forms import TFForm, CellTypeForm, FormFields
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
                'url_name': 'tracks-factors',
                'is_active': active_page == Navigation.TRACKS_PAGE,
            },
            {
                'label': Navigation.ABOUT_PAGE,
                'url_name': 'tracks-about',
                'is_active': active_page == Navigation.ABOUT_PAGE,
            },
        ]

class Steps(object):
    TRANSCRIPTION_FACTORS = 'Transcription Factors'
    CELL_TYPE = 'Cell Type'
    TRACK = 'Tracks'

    @staticmethod
    def make_items(active_step_name):
        items = []
        for step_name in [Steps.TRANSCRIPTION_FACTORS, Steps.CELL_TYPE, Steps.TRACK]:
            items.append({
                "label": step_name,
                "is_active": active_step_name == step_name,
            })
            if active_step_name == step_name:
                break

        return items
def get_template(template_filename):
    template_path = os.path.join(JINJA_TEMPLATE_DIR, template_filename)
    with open(template_path) as infile:
        return Template(infile.read())


def encode_key_dict(key_dict):
    parts = []
    for k, v in key_dict.items():
        parts.append(
            '{}_{}'.format(k, '_'.join(v))
        )
    return '__'.join(parts)


def decode_key_dict(encoded_str):
    key_dict = {}
    parts = encoded_str.split('__')
    for part in parts:
        key_values = part.split('_')
        key = key_values[0]
        values = [val for val in key_values[1:] if val]
        if values:
            key_dict[key] = values
    return key_dict


def index(request):
    return redirect('tracks-factors')

def about(request):
    template = loader.get_template('tracks/about.html')
    context = {
        'nav_title': Navigation.TITLE,
        'nav_items': Navigation.make_items(active_page=Navigation.ABOUT_PAGE),
    }
    return HttpResponse(template.render(context, request))


def get_request_data(request):
    if request.method == 'POST':
        return request.POST
    else:
        return request.GET


def make_field_name_query_params(form, name):
    return [name + '=' + str(field.pk) for field in form.cleaned_data[name]]


def select_factors(request):
    form = TFForm(get_request_data(request))
    if request.method == 'POST':
        if form.is_valid():
            query_param_ary = make_field_name_query_params(form, FormFields.TF_NAME)
            query_params = '?' + '&'.join(query_param_ary)
            return redirect(reverse('tracks-select_cell_type') + query_params)
    template = loader.get_template('tracks/select_factors.html')
    context = {
        'nav_title': Navigation.TITLE,
        'nav_items': Navigation.make_items(active_page=Navigation.TRACKS_PAGE),
        'step_items': Steps.make_items(Steps.TRANSCRIPTION_FACTORS),
        'form': form,
    }
    return HttpResponse(template.render(context, request))


def select_cell_type(request):
    form = CellTypeForm(get_request_data(request))
    template = loader.get_template('tracks/select_cell_type.html')
    if request.method == 'POST':
        if form.is_valid():
            query_param_ary = make_field_name_query_params(form, FormFields.TF_NAME)
            query_param_ary.extend(make_field_name_query_params(form, FormFields.CELL_TYPE))
            query_params = '?' + '&'.join(query_param_ary)
            return redirect(reverse('tracks-choose_combinations') + query_params)
    context = {
        'nav_title': Navigation.TITLE,
        'nav_items': Navigation.make_items(active_page=Navigation.TRACKS_PAGE),
        'step_items': Steps.make_items(Steps.CELL_TYPE),
        'form': form
    }
    return HttpResponse(template.render(context, request))


def choose_combinations(request):
    request_data = get_request_data(request)
    tfs = TranscriptionFactor.objects.filter(pk__in=request_data.getlist(FormFields.TF_NAME))
    celltypes = CellType.objects.filter(pk__in=request_data.getlist(FormFields.CELL_TYPE))
    context = {
        'nav_title': Navigation.TITLE,
        'nav_items': Navigation.make_items(active_page=Navigation.TRACKS_PAGE),
        'tfs': tfs,
        'step_items': Steps.make_items(Steps.TRACK),
        'celltypes': celltypes,
    }
    return render(request, 'tracks/choose_combinations.html', context)


def view_genome_browser(request):
    track_strs = request.POST.getlist("track_str")
    tf_celltype_pairs = [track_str.split(',') for track_str in track_strs]
    track_ids = []
    for tf, celltype in tf_celltype_pairs:
        for track in Track.objects.filter(tf__name=tf, cell_type__name=celltype):
            track_ids.append(str(track.id))

    encoded_key_value = '_'.join(track_ids)
    dynamic_hub_url = request.build_absolute_uri('/tracks/{}/hub.txt'.format(encoded_key_value))
    genome = Genome.objects.get()
    genome_browser_url = "https://genome.ucsc.edu/cgi-bin/hgTracks?org=human&db={}&hubUrl={}".format(
        genome.name, dynamic_hub_url
    )
    return redirect(genome_browser_url)


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
