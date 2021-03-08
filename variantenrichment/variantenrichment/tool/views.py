from django.shortcuts import render
from django.views.generic import DetailView
from django.views.generic.edit import FormView

from .models import (
    Project,
    VariantFile
)


class ProjectResultsView(DetailView):
    model = Project
    template_name = "pages/results.html"
