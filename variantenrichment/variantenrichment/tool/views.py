from time import sleep

from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from .forms import ConfirmProcessingForm, FilesDeleteForm, FilesChooseForm, SearchForm, ProjectForm
from django.views.generic import DetailView, FormView, TemplateView, View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from .models import (
    Project,
    BackgroundJob,
    VariantFile,
    ProjectFiles
)
from .tasks import annotate_task, check_cadd_task, filter_task


def get_project(pk):
    return Project.objects.get(pk=pk)


class ProjectCreateView(CreateView):
    model = Project
    template_name = "pages/project_create.html"
    fields = [
        'title', 'impact', 'frequency',
        'impact_exception', 'genes_exception', 'background',
        'filter_population', 'cadd_score', 'genes', 'inheritance'
    ]

    def get_success_url(self, **kwargs):
        return reverse_lazy(
            'project-detail',
            kwargs={'pk': self.object.pk}
        )


class ProjectDetailView(DetailView):
    model = Project
    template_name = "pages/project_detail.html"
    form_class = FilesChooseForm

    def post(self, request, *args, **kwargs):
        file_ids = []
        for key in request.POST.keys():
            if key.startswith("file_"):
                file_id = int(key.split("_", 1)[1])
                file_ids.append(file_id)

        self.request.session['selected_files'] = file_ids

        return redirect('files-delete', pk=self.kwargs['pk'])


class ProjectUpdateView(UpdateView):
    model = Project
    template_name = "pages/project_update.html"
    fields = [
        'title', 'impact', 'frequency',
        'impact_exception', 'genes_exception', 'background',
        'filter_population', 'cadd_score', 'genes', 'inheritance'
    ]

    def get_success_url(self, **kwargs):
        project = get_project(self.kwargs['pk'])
        print(project)
        if project.state != "initial" and project.state != "annotated":
            project.state = "annotated"
            project.save()

        return reverse_lazy(
            'project-detail',
            kwargs={'pk': self.object.pk}
        )


class FileUploadView(CreateView):
    model = VariantFile
    template_name = "pages/file_upload.html"
    fields = ['individual_name', 'uploaded_file']

    def get_success_url(self, **kwargs):
        project = get_project(self.kwargs['pk'])
        print(project)
        if project.state != "initial":
            project.state = "initial"
            project.save()

        return reverse_lazy(
            'project-detail',
            kwargs={'pk': self.kwargs['pk']}
        )

    def form_valid(self, form):
        form.instance.project = get_project(self.kwargs['pk'])
        return super().form_valid(form)


class FilesDeleteView(FormView):
    model = Project
    template_name = "pages/files_delete.html"
    form_class = FilesDeleteForm

    def get(self, request, *args, **kwargs):
        file_ids = self.request.session.get('selected_files')
        files = VariantFile.objects.filter(pk__in=file_ids)
        context = {
            'form': self.form_class,
            'selected_files': files,
            'pk': self.kwargs['pk']
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        file_ids = self.request.session.get('selected_files')

        if request.POST.get("delete_confirm"):
            VariantFile.objects.filter(pk__in=file_ids).delete()

            project = get_project(self.kwargs['pk'])
            print(project)
            if project.state != "initial":
                project.state = "initial"
                project.save()

            return redirect('project-detail', pk=self.kwargs['pk'])


class CheckCaddView(View):
    def get(self, *args, **kwargs):
        bj = BackgroundJob(
            name="Checking for CADD answer",
            project=Project.objects.get(uuid=self.kwargs['pk']),
            state="new"
        )
        bj.save()
        check_cadd_task.apply_async(args=[bj.pk], countdown=1)
        return redirect('project-detail', pk=self.kwargs['pk'])


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
        project_state = get_project(self.kwargs['pk']).state
        job_name = "Annotating" if project_state == "initial" else "Filtering"
        bj = BackgroundJob(
            name=job_name,
            project=Project.objects.get(uuid=self.kwargs['pk']),
            state="new"
        )
        bj.save()

        if project_state == "initial":
            annotate_task.apply_async(args=[bj.pk], countdown=1)
        else:
            filter_task.apply_async(args=[bj.pk], countdown=1)

        return super().form_valid(form)


class ProjectResultsView(TemplateView):
    template_name = "pages/project_results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_files = ProjectFiles.objects.get(project=Project.objects.get(uuid=self.kwargs['pk']))
        scores = []
        header = None

        with open(project_files.scores_csv) as scores_file:
            for line in scores_file:
                line = line.strip()
                line_arr = line.split(",")
                if not header:
                    line_arr[0] = "gene"
                    header = line_arr
                else:
                    scores.append(dict(zip(header, line_arr)))

        context["scores"] = scores
        return context


class SearchView(FormView):
    template_name = "pages/search.html"
    form_class = SearchForm

    def post(self, request, *args, **kwargs):
        search_id = request.POST.get("search-uuid")
        try:
            project = Project.objects.get(uuid=search_id)
        except (ValidationError, Project.DoesNotExist):
            project = 0

        print(search_id, project)
        context = {
            'project': project,
            'form': self.form_class,
        }
        return render(request, self.template_name, context)
