from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DNASequence
from .serializers import DNASequenceSerializer, DNASequenceUploadSerializer


class DNASequenceUploadView(APIView):
    """
    Endpoint para cargar una secuencia desde archivo CSV/FASTA/TXT.
    """

    def post(self, request, *args, **kwargs):
        serializer = DNASequenceUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        sequence = serializer.save()
        response_serializer = DNASequenceSerializer(sequence)
        created = status.HTTP_201_CREATED if getattr(serializer, 'was_created', True) else status.HTTP_200_OK
        return Response(response_serializer.data, status=created)


class DNASequenceListView(generics.ListAPIView):
    """
    Lista las secuencias almacenadas (paginable).
    """

    queryset = DNASequence.objects.all().order_by('-uploaded_at')
    serializer_class = DNASequenceSerializer

# Create your views here.
