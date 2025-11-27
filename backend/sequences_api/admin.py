from django.contrib import admin

from .models import DNASequence


@admin.register(DNASequence)
class DNASequenceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'length', 'uploaded_at')
    search_fields = ('name', 'file_hash')
    list_filter = ('uploaded_at',)
    ordering = ('-uploaded_at',)
