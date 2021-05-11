from django.forms import Form, ModelForm
from .models import Project, VariantFile


class ConfirmProcessingForm(Form):
    # name = forms.CharField()
    pass


class FilesDeleteForm(Form):
    pass


class FilesChooseForm(Form):
    pass


class SearchForm(Form):
    pass
