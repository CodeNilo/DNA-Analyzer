import hashlib

from django.db import models
from django.utils import timezone

from .validators import normalize_sequence, validate_dna_sequence

class DNASequence(models.Model):
    
    name = models.CharField(max_length=255, help_text="Nombre del archivo")
    sequence = models.TextField(help_text="Secuencia de ADN (A, T, C, G, N)")
    length = models.PositiveIntegerField(help_text="Longitud de la secuencia")
    uploaded_at = models.DateTimeField(default=timezone.now, help_text="Fecha y hora de subida")
    file_hash = models.CharField(max_length=64, unique=True, help_text="Hash SHA-256 del archivo para evitar duplicados")
    gc_content = models.FloatField(null=True, blank=True, help_text="Porcentaje de G/C en la secuencia")
    
    # Metadata del Modelo
    class Meta:
        db_table = "dna_sequences"
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["uploaded_at"]),
            models.Index(fields=["file_hash"]),
        ]
        verbose_name = "DNA Sequence"
        verbose_name_plural = "DNA Sequences"
    
    def __str__(self):
        return f"{self.name} ({self.length} bp)"
    
    def save(self, *args, **kwargs):
        # Normalizamos y validamos antes de guardar
        self.sequence = validate_dna_sequence(normalize_sequence(self.sequence))
        if not self.length:
            self.length = len(self.sequence)
        if self.gc_content is None:
            if self.length > 0:
                gc = sum(1 for c in self.sequence if c in ('G', 'C'))
                self.gc_content = (gc / self.length) * 100
            else:
                self.gc_content = 0
        if not self.file_hash:
            self.file_hash = hashlib.sha256(self.sequence.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)
