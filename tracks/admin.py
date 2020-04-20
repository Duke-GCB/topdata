from django.contrib import admin

from tracks.models import *

admin.site.register(Genome)
admin.site.register(Track)
admin.site.register(TranscriptionFactor)
admin.site.register(CellType)
admin.site.register(RepName)
