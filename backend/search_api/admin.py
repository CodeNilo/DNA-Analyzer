from django.contrib import admin

from .models import SearchJob, SearchResult


@admin.register(SearchJob)
class SearchJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'sequence', 'pattern', 'status', 'total_matches', 'algorithm_used', 'created_at')
    list_filter = ('status', 'algorithm_used', 'created_at')
    search_fields = ('pattern', 'sequence__name')
    ordering = ('-created_at',)


@admin.register(SearchResult)
class SearchResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'position')
    list_filter = ('job',)
    search_fields = ('job__pattern',)

# Register your models here.
