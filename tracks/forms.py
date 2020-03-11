from django import forms
from tracks.models import TranscriptionFactor, CellType


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
            widget=forms.SelectMultiple(attrs={'class':'form-control topdata-large-vertical'}),
            required = False,
            label="Select one or more transcription factors",
        )


class CellTypeForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(CellTypeForm, self).__init__(*args, **kwargs)
        self.fields[FormFields.CELL_TYPE] = ModelMultipleChoiceField(
            queryset=CellType.objects.order_by('name'),
            widget=forms.SelectMultiple(attrs={'class':'form-control topdata-large-vertical'}),
            required = False,
            label="Select cell types",
        )
        self.fields[FormFields.TF_NAME] = ModelMultipleChoiceField(
            queryset=TranscriptionFactor.objects.order_by('name'),
            widget=forms.MultipleHiddenInput(),
            required = True,
            label="Select one or more transcription factors",
        )
