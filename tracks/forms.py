from django import forms
from django.conf import settings
from django.forms.utils import ErrorList
from django.utils.html import format_html_join, format_html
from tracks.models import TranscriptionFactor, CellType, Track

FORM_CONTROL_ATTRS = {'class':'form-control', 'size':'20'}


class FormFields(object):
    TF_NAME = 'tf'
    CELL_TYPE = 'celltype'


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


class TFForm(forms.Form):
    error_css_class = "invalid-feedback"

    def __init__(self, data):
        super(TFForm, self).__init__(data, error_class=BootstrapErrorList)
        self.fields[FormFields.TF_NAME] = ModelMultipleChoiceField(
            queryset=TranscriptionFactor.objects.order_by('name'),
            widget=forms.SelectMultiple(attrs=FORM_CONTROL_ATTRS),
            required = False,
            label="Select one or more transcription factors",
        )


class CellTypeForm(forms.Form):
    def __init__(self, data, request_method):
        super(CellTypeForm, self).__init__(data, error_class=BootstrapErrorList)
        self.fields[FormFields.CELL_TYPE] = ModelMultipleChoiceField(
            queryset=CellType.objects.order_by('name'),
            widget=forms.SelectMultiple(attrs=FORM_CONTROL_ATTRS),
            required = False,
            label="Select one or more cell types",
        )
        self.fields[FormFields.TF_NAME] = ModelMultipleChoiceField(
            queryset=TranscriptionFactor.objects.order_by('name'),
            widget=forms.MultipleHiddenInput(),
            required = True,
            label="Select one or more transcription factors",
        )
        self.request_method = request_method

    def clean(self):
        cleaned_data = super().clean()
        if self.request_method == 'POST':
            num_tracks = Track.objects.filter(
                tf__name__in=cleaned_data.get(FormFields.TF_NAME),
                cell_type__name__in=cleaned_data.get(FormFields.CELL_TYPE),
            ).count()
            if num_tracks > settings.TRACK_SELECTION_LIMIT:
                msg = "Too many cell types selected. Your selection resulted in {} tracks. Max allowed is {}.".format(
                    num_tracks, settings.TRACK_SELECTION_LIMIT
                )
                raise forms.ValidationError(msg)
