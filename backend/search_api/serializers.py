from rest_framework import serializers

from sequences_api.models import DNASequence
from sequences_api.validators import normalize_sequence, validate_dna_sequence
from .models import SearchJob, SearchResult


class SearchRequestSerializer(serializers.Serializer):
    sequence_id = serializers.IntegerField()
    pattern = serializers.CharField(max_length=1000)
    allow_overlapping = serializers.BooleanField(default=True)

    def validate_pattern(self, value):
        normalized = normalize_sequence(value)
        return validate_dna_sequence(normalized)

    def validate_sequence_id(self, value):
        if not DNASequence.objects.filter(pk=value).exists():
            raise serializers.ValidationError("La secuencia especificada no existe.")
        return value


class SearchResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchResult
        fields = ['position', 'context_before', 'context_after']


class SearchJobSerializer(serializers.ModelSerializer):
    sequence_name = serializers.CharField(source='sequence.name', read_only=True)

    class Meta:
        model = SearchJob
        fields = [
            'id',
            'sequence',
            'sequence_name',
            'pattern',
            'allow_overlapping',
            'status',
            'total_matches',
            'search_time_ms',
            'algorithm_used',
            'created_at',
            'completed_at',
        ]
