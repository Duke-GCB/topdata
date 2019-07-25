from django.http import HttpResponse
from django.template import loader
from jinja2 import Template
from django.shortcuts import redirect
from tracks.models import Track
from tracks.forms import NameForm
import os


SPLIT_ARY_SEP = '+'
HUB_NAME_ITEM_SEP = '__'
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
        values = key_values[1:]
        if values:
            key_dict[key] = values
    return key_dict


def index(request):
    form = NameForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            data = {}
            for k,v in form.cleaned_data.items():
                data[k] = [x.name for x in v]

            encoded_key_values = encode_key_dict(data)
            return redirect('/tracks/{}/'.format(encoded_key_values))

    template = loader.get_template('tracks/index.html')
    context = {
        'form': form
    }
    return HttpResponse(template.render(context, request))


def get_tracks(encoded_key_value):
    key_dict = decode_key_dict(encoded_key_value)
    query = Track.objects.all()
    tf_names = key_dict.get(NameForm.TF_NAME)
    if tf_names:
        query = query.filter(tf_name__name__in=tf_names)
    cell_types = key_dict.get(NameForm.CELL_TYPE)
    if cell_types:
        query = query.filter(cell_type__name__in=cell_types)
    rep_names = key_dict.get(NameForm.REP_NAME)
    if rep_names:
        query = query.filter(rep_name__name__in=rep_names)
    return query


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
    data = template.render(context)
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
