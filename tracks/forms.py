from django import forms
from django.conf import settings
from tracks.models import TranscriptionFactor, CellType, Track

FORM_CONTROL_ATTRS = {'class':'form-control topdata-large-vertical'}


class FormFields(object):
    TF_NAME = 'tf'
    CELL_TYPE = 'celltype'


class ModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class TFForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(TFForm, self).__init__(*args, **kwargs)
        self.fields[FormFields.TF_NAME] = ModelMultipleChoiceField(
            queryset=TranscriptionFactor.objects.order_by('name'),
            widget=forms.SelectMultiple(attrs=FORM_CONTROL_ATTRS),
            required = False,
            label="Select one or more transcription factors",
        )


class CellTypeForm(forms.Form):
    def __init__(self, data, request_method):
        super(CellTypeForm, self).__init__(data)
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
                msg = "You many only select {} total tracks. " \
                      "You have selected {} tracks.".format(
                    settings.TRACK_SELECTION_LIMIT, num_tracks
                )
                raise forms.ValidationError(msg)
