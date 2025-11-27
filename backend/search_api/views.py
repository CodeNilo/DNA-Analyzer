from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from sequences_api.models import DNASequence
from .models import SearchJob, SearchResult
from .serializers import SearchJobSerializer, SearchRequestSerializer, SearchResultSerializer
from .services import run_search


class SearchView(APIView):
    """
    Endpoint de búsqueda inicial (sin microservicio, búsqueda local naive).
    """

    def post(self, request, *args, **kwargs):
        req_serializer = SearchRequestSerializer(data=request.data)
        if not req_serializer.is_valid():
            return Response(req_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        sequence_id = req_serializer.validated_data['sequence_id']
        pattern = req_serializer.validated_data['pattern']
        allow_overlapping = req_serializer.validated_data['allow_overlapping']

        sequence = DNASequence.objects.get(pk=sequence_id)

        # Creamos el job y ejecutamos búsqueda local en la misma petición
        job = SearchJob.objects.create(
            sequence=sequence,
            pattern=pattern,
            allow_overlapping=allow_overlapping,
            status='PROCESSING',
        )

        try:
            import time
            t0 = time.perf_counter()
            result_data = run_search(sequence.sequence, pattern, allow_overlapping)
            end_to_end_ms = (time.perf_counter() - t0) * 1000
            matches = result_data['matches']

            # Guardamos resultados asociados al job
            with transaction.atomic():
                SearchResult.objects.bulk_create([
                    SearchResult(
                        job=job,
                        position=match['position'],
                        context_before=match['context_before'],
                        context_after=match['context_after'],
                    )
                    for match in matches
                ])

                job.mark_as_completed(
                    total_matches=result_data['total_matches'],
                    search_time_ms=result_data['search_time_ms'],
                    algorithm_used=result_data['algorithm_used'],
                )

        except Exception as exc:  # pylint: disable=broad-except
            job.mark_as_failed(str(exc))
            return Response(
                {'detail': f'Error durante la búsqueda: {exc}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Serializamos respuesta con resumen y primeros resultados
        job_data = SearchJobSerializer(job).data
        top_results = SearchResultSerializer(job.results.all()[:100], many=True).data

        return Response(
            {
                'job': job_data,
                'results': top_results,
                'end_to_end_ms': end_to_end_ms,
                'search_time_ms': result_data.get('search_time_ms'),
            },
            status=status.HTTP_200_OK,
        )


class SearchJobDetailView(generics.RetrieveAPIView):
    """
    Permite consultar un job y sus resultados (limitados).
    """

    queryset = SearchJob.objects.all()
    serializer_class = SearchJobSerializer

    def retrieve(self, request, *args, **kwargs):
        job = self.get_object()
        limit = int(request.query_params.get('limit', 100))
        limit = max(1, min(limit, 500))
        results = SearchResultSerializer(job.results.all()[:limit], many=True).data
        job_data = self.get_serializer(job).data
        return Response(
            {
                'job': job_data,
                'results': results,
            },
            status=status.HTTP_200_OK,
        )

# Create your views here.
