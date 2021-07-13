import uuid
from django.db import models


def get_vcf_directory(instance, filename):
    return 'projects/{0}/vcf/{1}'.format(instance.project.uuid, filename)


def get_project_directory(instance, filename):
    return 'projects/{0}/{1}'.format(instance.uuid, filename)


def get_default_bgset():
    """ get a default value for result status; create new result if not available """
    return BackgroundSet.objects.get_or_create(name="IGSR")[0]


class BackgroundSet(models.Model):
    """ Describes background data set
        file and population fields are paths to corresponding files on server
    """
    name = models.CharField(max_length=30, unique=True)
    file = models.CharField(max_length=200)
    population = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name


class Project(models.Model):
    """ Stores all information about user defined project settings
    """
    STATE_CHOICES = [
        ('initial', 'Initial'),
        ('annotating', 'Annotating variants'),
        ('annotated', 'Ready for filtering'),
        ('filtering', 'Filtering data sets'),
        ('cadd-waiting', 'Waiting for CADD answer'),
        ('cadd-checking', 'Checking if CADD scores are ready'),
        ('cadd-filtering', 'Annotating with CADD functional scores and filtering data sets by PHRED cutoff'),
        ('analyzing', 'Analyzing datasets and computing statistics'),
        ('done', 'Done')
    ]
    IMPACT_CHOICES = [
        ('MODERATE', 'Moderate'),
        ('HIGH', 'High')
    ]

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4(),
        editable=False)
    title = models.CharField(max_length=100)
    state = models.CharField(
        max_length=15,
        choices=STATE_CHOICES,
        default='initial'
    )
    impact = models.CharField(
        max_length=10,
        choices=IMPACT_CHOICES,
        default='MODERATE'
    )
    impact_exception = models.CharField(
        max_length=10,
        choices=IMPACT_CHOICES,
        blank=True
    )
    genes_exception = models.CharField(
        max_length=200,
        blank=True
    )
    frequency = models.DecimalField(
        max_digits=6,
        decimal_places=5,
        default=0.001)
    background = models.ForeignKey(
        BackgroundSet,
        default=get_default_bgset,
        on_delete=models.SET_DEFAULT)
    filter_population = models.BooleanField(default=False)
    cadd_score = models.IntegerField(null=True, blank=True)
    genes = models.FileField(upload_to=get_project_directory, blank=True)
    inheritance = models.FileField(upload_to=get_project_directory)

    def __str__(self):
        return self.title + ': ' + self.state


class VariantFile(models.Model):
    """ Describes individual vcfs uploaded to the Project
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    individual_name = models.CharField(max_length=20)  # user defined?
    uploaded_file = models.FileField(upload_to=get_vcf_directory)

    def __str__(self):
        return self.individual_name


class ProjectFiles(models.Model):
    """ Stores paths to last created case and control files,
        CADD job ids and paths to downloaded CADD tsv files
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    case_annotated = models.CharField(max_length=200)
    case_filtered = models.CharField(max_length=200, blank=True)
    control_filtered = models.CharField(max_length=200, blank=True)
    cadd_case_id = models.CharField(max_length=60, blank=True)
    cadd_case = models.CharField(max_length=200, blank=True)
    cadd_control_id = models.CharField(max_length=60, blank=True)
    cadd_control = models.CharField(max_length=200, blank=True)
    case_csv = models.CharField(max_length=200, blank=True)
    control_csv = models.CharField(max_length=200, blank=True)
    scores_csv = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.case_annotated


class BackgroundJob(models.Model):
    """ Describes jobs that are passed to Celery to run as background tasks
    """
    STATE_CHOICES = [
        ('new', 'New'),
        ('running', 'Running'),
        ('done', 'Finished'),
        ('error', 'Error')
    ]

    name = models.CharField(max_length=30)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE
    )
    state = models.CharField(
        max_length=7,
        choices=STATE_CHOICES,
        default='new'
    )

    def __str__(self):
        return self.name + ': ' + self.state
