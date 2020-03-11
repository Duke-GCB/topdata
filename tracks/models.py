from django.db import models


class Genome(models.Model):
    """
    A genome that a track exists in. Example: hg19.
    """
    name = models.CharField(primary_key=True, max_length=255, unique=True, help_text="Name of the genome")
    def __str__(self):
        return "Genome - pk: {}".format(self.pk)


class TranscriptionFactor(models.Model):
    name = models.CharField(primary_key=True, max_length=255, unique=True, help_text="Name of the transcription factor")
    def __str__(self):
        return "TranscriptionFactor - pk: {}".format(self.pk)


class CellType(models.Model):
    name = models.CharField(primary_key=True, max_length=255, unique=True, help_text="Name of the cell type")
    def __str__(self):
        return "CellType - pk: {}".format(self.pk)


class RepName(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text="Replicate name")
    def __str__(self):
        return "RepName - pk: {} name: '{}'".format(self.pk, self.name)


class Track(models.Model):
    """
    Contains tags associated with this track and url to a file that will be used by trackhub.
    """
    genome = models.ForeignKey(Genome, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, unique=True, help_text="Name of the track")
    short_label = models.CharField(max_length=255, help_text="Short label used in trackDb.txt")
    long_label = models.CharField(max_length=255, help_text="Long label used in trackDb.txt")
    big_data_url = models.URLField(help_text="URL used for bigDataUrl in trackDb.txt", max_length=1000)
    file_type = models.CharField(max_length=255, help_text="Type of file referenced by big_data_url")
    tf = models.ForeignKey(TranscriptionFactor, on_delete=models.CASCADE, help_text="Transcription factor")
    cell_type = models.ForeignKey(CellType, on_delete=models.CASCADE, help_text="Cell type")
    rep_name = models.ForeignKey(RepName, on_delete=models.CASCADE, help_text="Replicate name")
    def __str__(self):
        return "Track - pk: {} genome: '{}' name: '{}'".format(self.pk, self.genome.name, self.name)

    class Meta:
        unique_together = ('genome', 'name',)
