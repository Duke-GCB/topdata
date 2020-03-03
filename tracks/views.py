from django.http import HttpResponse
from django.template import loader
from django.db.models import Q
from jinja2 import Template
from django.shortcuts import redirect, render
from tracks.models import Track, TFName, CellType, Genome
from tracks.forms import TFForm, CellTypeForm, FormFields
import os


TEMPLATE_CONFIG = 'templates.yaml'
JINJA_TEMPLATE_DIR = 'jinja2'


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
    return redirect('/tracks/select-factors/')


def select_factors(request):
    form = TFForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            data = {}
            for k,v in form.cleaned_data.items():
                data[k] = [x.name for x in v]

            encoded_key_values = encode_key_dict(data)
            return redirect('/tracks/{}/'.format(encoded_key_values))

    template = loader.get_template('tracks/select_factors.html')
    context = {
        'form': form
    }
    return HttpResponse(template.render(context, request))


def select_cell_type(request):
    form = CellTypeForm(request.POST or None)
    template = loader.get_template('tracks/select_cell_type.html')
    context = {
        'form': form
    }
    return HttpResponse(template.render(context, request))


def choose_combinations(request):
    tfnames = TFName.objects.filter(id__in=request.POST.getlist(FormFields.TF_NAME))
    celltypes = CellType.objects.filter(id__in=request.POST.getlist(FormFields.CELL_TYPE))
    context = {
        'tfnames': tfnames,
        'celltypes': celltypes,
    }
    print(context)
    return render(request, 'tracks/choose_combinations.html', context)


def view_genome_browser(request):
    track_strs = request.POST.getlist("track_str")
    tf_celltype_pairs = [track_str.split(',') for track_str in track_strs]
    track_ids = []
    for tf, celltype in tf_celltype_pairs:
        for track in Track.objects.filter(tf_name__name=tf, cell_type__name=celltype):
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
