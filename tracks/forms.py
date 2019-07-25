from django import forms
from tracks.models import TFName, CellType, RepName


class ModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class NameForm(forms.Form):
    TF_NAME = 'tfname'
    CELL_TYPE = 'celltype'
    REP_NAME = 'rep'
    NAME_FIELDS = [TF_NAME, CELL_TYPE, REP_NAME]

    def __init__(self, *args, **kwargs):
        super(NameForm, self).__init__(*args, **kwargs)
        self.fields[self.TF_NAME] = ModelMultipleChoiceField(
            queryset=TFName.objects.order_by('name'),
            widget=forms.CheckboxSelectMultiple(),
            required = False,
        )
        self.fields[self.CELL_TYPE] = ModelMultipleChoiceField(
            queryset=CellType.objects.order_by('name'),
            widget=forms.CheckboxSelectMultiple(),
            required = False,
        )
        self.fields[self.REP_NAME] = ModelMultipleChoiceField(
            queryset=RepName.objects.order_by('name'),
            widget=forms.CheckboxSelectMultiple(),
            required = False,
        )
