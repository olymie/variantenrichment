from django.forms import Form, ModelForm, HiddenInput
from .models import Project, VariantFile


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = [
            'title', 'impact', 'frequency',
            'impact_exception', 'genes_exception', 'background',
            'population', 'cadd_score', 'genes', 'inheritance'
        ]
        widgets = {'population': HiddenInput()}


class ConfirmProcessingForm(Form):
    # name = forms.CharField()
    pass


class FilesDeleteForm(Form):
    pass


class FilesChooseForm(Form):
    pass


class SearchForm(Form):
    pass
