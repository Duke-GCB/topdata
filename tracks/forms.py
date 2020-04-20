from django import forms
from django.conf import settings
from django.forms.utils import ErrorList
from django.utils.html import format_html_join, format_html, quote
from django.shortcuts import reverse
from tracks.models import TranscriptionFactor, CellType, Track, Genome
from django.core.exceptions import ValidationError

FORM_CONTROL_ATTRS = {'class':'form-control', 'size':'20'}


class FormFields(object):
    TF_NAME = 'tf'
    CELL_TYPE = 'celltype'
    TRACK_STR = 'track_str'


class ModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name

class BootstrapErrorList(ErrorList):
    def as_ul(self):
        if not self.data:
            return ''

        return format_html(
            '<ul class="{} alert alert-warning">{}</ul>',
            self.error_class,
            format_html_join('', '<li class="d-block">{}</li>', ((e,) for e in self)))


def make_field_name_query_params(form, name):
    return [name + '=' + quote(field.pk) for field in form.cleaned_data[name]]


def make_step_url(view_name, query_param_ary):
    query_params = '?' + '&'.join(query_param_ary)
    return reverse(view_name) + query_params


class TranscriptionFactorForm(forms.Form):
    error_css_class = "invalid-feedback"

    def __init__(self, *args, **kwargs):
        super(TranscriptionFactorForm, self).__init__(*args, **kwargs, error_class=BootstrapErrorList)
        self.fields[FormFields.TF_NAME] = ModelMultipleChoiceField(
            queryset=TranscriptionFactor.objects.order_by('name'),
            widget=forms.SelectMultiple(attrs=FORM_CONTROL_ATTRS),
            label="Select one or more transcription factors",
        )

    def next_step_url(self):
        query_param_ary = make_field_name_query_params(self, FormFields.TF_NAME)
        return make_step_url('tracks-select_cell_type', query_param_ary)


class CellTypeForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(CellTypeForm, self).__init__(*args, **kwargs, error_class=BootstrapErrorList)
        self.fields[FormFields.CELL_TYPE] = ModelMultipleChoiceField(
            queryset=CellType.objects.order_by('name'),
            widget=forms.SelectMultiple(attrs=FORM_CONTROL_ATTRS),
            label="Select one or more cell types",
        )
        self.fields[FormFields.TF_NAME] = ModelMultipleChoiceField(
            queryset=TranscriptionFactor.objects.order_by('name'),
            widget=forms.MultipleHiddenInput(),
            required=False,
            label="Select one or more transcription factors",
        )

    def clean(self):
        cleaned_data = super().clean()
        tfs = cleaned_data.get(FormFields.TF_NAME)
        cell_types = cleaned_data.get(FormFields.CELL_TYPE)
        if tfs and cell_types:
            num_tracks = Track.objects.filter(
                tf__name__in=cleaned_data.get(FormFields.TF_NAME),
                cell_type__name__in=cleaned_data.get(FormFields.CELL_TYPE),
            ).count()
            if num_tracks > settings.TRACK_SELECTION_LIMIT:
                msg = "Too many cell types selected. Your selection resulted in {} tracks. Max allowed is {}.".format(
                    num_tracks, settings.TRACK_SELECTION_LIMIT
                )
                raise forms.ValidationError(msg)

    def next_step_url(self):
        query_param_ary = make_field_name_query_params(self, FormFields.TF_NAME)
        query_param_ary.extend(make_field_name_query_params(self, FormFields.CELL_TYPE))
        return make_step_url('tracks-select_tracks', query_param_ary)


class TracksMultipleChoiceField(forms.MultipleChoiceField):
    # each track is represented as a string consisting of TF and a cell type seperated by a comma
    def validate(self, value):
        if self.required and not value:
            raise ValidationError(self.error_messages['required'], code='required')
        # Validate that each value in the value list is a valid tf and cell type combination
        for val in value:
            if not ',' in val:
                raise ValidationError(
                    'Invalid track value {}'.format(val),
                    code='invalid_choice',
                    params={'value': val},
                )
            tf, cell_type = val.split(',')
            try:
                TranscriptionFactor.objects.get(pk=tf)
                CellType.objects.get(pk=cell_type)
            except (TranscriptionFactor.DoesNotExist, CellType.DoesNotExist):
                raise ValidationError(
                    self.error_messages['invalid_choice'],
                    code='invalid_choice',
                    params={'value': val},
                )


class TracksForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(TracksForm, self).__init__(*args, **kwargs, error_class=BootstrapErrorList)
        self.fields[FormFields.TRACK_STR] = TracksMultipleChoiceField(
            widget=forms.CheckboxSelectMultiple(),
        )

    @staticmethod
    def get_position_from_first_track(tf_cell_type_pairs):
        first_tf, first_cell_type = tf_cell_type_pairs[0]
        track = Track.objects.filter(tf__name=first_tf, cell_type__name=first_cell_type)[0]
        return track.position

    @staticmethod
    def get_track_ids(tf_cell_type_pairs):
        track_ids = []
        for tf, cell_type in tf_cell_type_pairs:
            for track in Track.objects.filter(tf__name=tf, cell_type__name=cell_type):
                track_ids.append(str(track.id))
        return track_ids

    def next_step_url(self, request):
        track_strs = self.cleaned_data[FormFields.TRACK_STR]
        tf_cell_type_pairs = [track_str.split(',') for track_str in track_strs]
        position = self.get_position_from_first_track(tf_cell_type_pairs)
        track_ids = self.get_track_ids(tf_cell_type_pairs)
        encoded_key_value = '_'.join(track_ids)
        dynamic_hub_url = request.build_absolute_uri('/tracks/{}/hub.txt'.format(encoded_key_value))
        genome = Genome.objects.get()
        genome_browser_url = "https://genome.ucsc.edu/cgi-bin/hgTracks?org=human&db={}&hubUrl={}".format(
            genome.name, dynamic_hub_url
        )
        if position:
            genome_browser_url += "&position={}".format(position)
        return genome_browser_url
