from django.db import models
from django.utils import timezone
from sequences_api.models import DNASequence


class SearchJob(models.Model):
    """
    Modelo para registrar trabajos de búsqueda de patrones en secuencias de ADN.
    """

    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('PROCESSING', 'En Proceso'),
        ('COMPLETED', 'Completado'),
        ('FAILED', 'Fallido'),
    ]
    
    sequence = models.ForeignKey(DNASequence, on_delete=models.CASCADE, related_name='search_jobs', help_text="Secuencia de ADN donde se busca")
    
    pattern = models.CharField(
        max_length=1000,
        help_text="Patrón a buscar (subsecuencia de ADN)"
    )

    allow_overlapping = models.BooleanField(
        default=True,
        help_text="Permitir coincidencias solapadas"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text="Estado actual del trabajo"
    )

    total_matches = models.IntegerField(
        null=True,
        blank=True,
        help_text="Total de coincidencias encontradas"
    )

    search_time_ms = models.FloatField(
        null=True,
        blank=True,
        help_text="Tiempo de búsqueda en milisegundos"
    )

    algorithm_used = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Algoritmo utilizado (KMP, Boyer-Moore, etc.)"
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha y hora de creación del trabajo"
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora de finalización"
    )

    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Mensaje de error si el trabajo falló"
    )
    
    class Meta:
        db_table = 'search_jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['sequence', 'pattern']),
        ]

        verbose_name = 'Search Job'
        verbose_name_plural = 'Search Jobs'
    
    def __str__(self):
        return f"Search '{self.pattern}' in {self.sequence.name} ({self.status})"
    
    def mark_as_processing(self):
        """Marca el trabajo como en proceso."""
        self.status = 'PROCESSING'
        self.save()
    
    def mark_as_completed(self, total_matches, search_time_ms, algorithm_used):
        """Marca el trabajo como completado con resultados."""
        self.status = 'COMPLETED'
        self.total_matches = total_matches
        self.search_time_ms = search_time_ms
        self.algorithm_used = algorithm_used
        self.completed_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, error_message):
        """Marca el trabajo como fallido con mensaje de error."""
        self.status = 'FAILED'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()


class SearchResult(models.Model):
    """
    Modelo para almacenar cada coincidencia encontrada en una búsqueda.
    """
    job = models.ForeignKey(
        SearchJob,
        on_delete=models.CASCADE,
        related_name='results',
        help_text="Trabajo de búsqueda al que pertenece este resultado"
    )

    position = models.BigIntegerField(
        help_text="Posición donde se encontró el patrón (índice base 0)"
    )

    context_before = models.CharField(
        max_length=50,
        blank=True,
        help_text="Nucleótidos antes del patrón (para contexto)"
    )
    
    context_after = models.CharField(
        max_length=50,
        blank=True,
        help_text="Nucleótidos después del patrón (para contexto)"
    )
    
    class Meta:
        db_table = 'search_results'
        ordering = ['position']
        indexes = [
            models.Index(fields=['job', 'position']),
        ]
        verbose_name = 'Search Result'
        verbose_name_plural = 'Search Results'
    
    def __str__(self):
        return f"Match at position {self.position} in job #{self.job.id}"