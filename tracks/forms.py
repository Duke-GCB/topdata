from django import forms
from tracks.models import TFName, CellType, RepName


class FormFields(object):
    TF_NAME = 'tfname'
    CELL_TYPE = 'celltype'


class ModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class TFForm(forms.Form):
    TF_NAME = 'tfname'

    def __init__(self, *args, **kwargs):
        super(TFForm, self).__init__(*args, **kwargs)
        self.fields[FormFields.TF_NAME] = ModelMultipleChoiceField(
            queryset=TFName.objects.order_by('name'),
            widget=forms.SelectMultiple(attrs={'class':'form-control topdata-large-vertical'}),
            required = True,
            label="Select one or more transcription factors",
        )


class CellTypeForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(CellTypeForm, self).__init__(*args, **kwargs)
        self.fields[FormFields.CELL_TYPE] = ModelMultipleChoiceField(
            queryset=CellType.objects.order_by('name'),
            widget=forms.SelectMultiple(attrs={'class':'form-control topdata-large-vertical'}),
            required = True,
            label="Select cell types",
        )
        self.fields[FormFields.TF_NAME] = ModelMultipleChoiceField(
            queryset=TFName.objects.order_by('name'),
            widget=forms.MultipleHiddenInput(),
            required = True,
            label="Select one or more transcription factors",
        )
