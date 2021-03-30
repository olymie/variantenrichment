from django.shortcuts import render
from .forms import ConfirmProcessingForm
from django.views.generic import View, DetailView, FormView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from .models import (
    Project,
    BackgroundJob,
    VariantFile
)

from .tasks import change_project_state_task


class ProjectCreateView(CreateView):
    model = Project
    template_name = "pages/project_create.html"
    fields = [
        'title', 'impact', 'frequency', 'background',
        'filter_population', 'cadd_score',
        'mutation_taster_score', 'genes'
    ]

    def get_success_url(self, **kwargs):
        return reverse_lazy(
            'project-detail',
            kwargs={'pk': self.object.pk}
        )


class ProjectDetailView(DetailView):
    model = Project
    template_name = "pages/project_detail.html"


class ProjectUpdateView(UpdateView):
    model = Project
    template_name = "pages/project_update.html"
    fields = [
        'title', 'impact', 'frequency', 'background',
        'filter_population', 'cadd_score',
        'mutation_taster_score', 'genes'
    ]

    def get_success_url(self, **kwargs):
        return reverse_lazy(
            'project-detail',
            kwargs={'pk': self.object.pk}
        )


class FileUploadView(CreateView):
    model = VariantFile
    template_name = "pages/file_upload.html"
    fields = ['individual_name', 'uploaded_file', 'population']

    def get_project(self):
        return Project.objects.get(pk=self.kwargs.get('pk'))

    def get_success_url(self, **kwargs):
        return reverse_lazy(
            'project-detail',
            kwargs={'pk': self.kwargs['pk']}
        )

    def form_valid(self, form):
        form.instance.project = self.get_project()
        return super().form_valid(form)


# class FileManage(FormView):



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
