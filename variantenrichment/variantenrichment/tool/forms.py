from django.forms import Form, ModelForm, HiddenInput, CheckboxSelectMultiple, TypedMultipleChoiceField
from .models import Project


class ProjectForm(ModelForm):
    population = TypedMultipleChoiceField(choices=[
            ("AFR", "African"),
            ("AMR", "American"),
            ("EAS", "East Asian"),
            ("EUR", "European"),
            ("SAS", "South Asian"),
        ],
        required=False,
        widget=CheckboxSelectMultiple)

    class Meta:
        model = Project
        fields = [
            'title', 'impact', 'frequency',
            'impact_exception', 'genes_exception', 'background',
            'population', 'cadd_score', 'genes', 'inheritance'
        ]


class ConfirmProcessingForm(Form):
    # name = forms.CharField()
    pass


class FilesDeleteForm(Form):
    pass


class FilesChooseForm(Form):
    pass


class SearchForm(Form):
    pass
