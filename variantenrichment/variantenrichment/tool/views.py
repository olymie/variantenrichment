from django.shortcuts import render
from .forms import ConfirmProcessingForm
from django.views.generic import DetailView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from time import sleep

from .models import (
    Project,
    BackgroundJob,
    VariantFile
)

from .tasks import change_project_state_task


class ProjectDetailView(DetailView):
    model = Project
    template_name = "pages/project_detail.html"


class ConfirmProcessingView(FormView):
    model = Project
    form_class = ConfirmProcessingForm
    template_name = "pages/confirm_processing.html"

    def get_success_url(self, **kwargs):
        return reverse_lazy(
            'project-detail',
            kwargs={'pk': self.kwargs['pk']}
        )

    def form_valid(self, form, **kwargs):
        bj = BackgroundJob(
            name="Test Job",
            project=Project.objects.get(uuid = self.kwargs['pk']),
            state="new"
        )
        bj.save()
        change_project_state_task.apply_async(args=[bj.pk], countdown=1)
        return super().form_valid(form)
