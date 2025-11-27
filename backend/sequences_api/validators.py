import re
from rest_framework import serializers

# Patrón: solo A, T, C, G, N (mayúsculas o minúsculas)
DNA_PATTERN = re.compile(r'^[ATCGN]+$')


def normalize_sequence(raw_text: str) -> str:
    """
    Limpia y normaliza el texto de entrada:
    - Convierte a mayúsculas
    - Remueve espacios y saltos de línea
    """
    if raw_text is None:
        return ''
    # Eliminamos espacios en blanco y saltos de línea
    cleaned = ''.join(raw_text.split())
    return cleaned.upper()


def validate_dna_sequence(seq: str) -> str:
    """
    Valida que la secuencia contenga únicamente nucleótidos válidos.
    Lanza ValidationError si no cumple.
    """
    if not seq:
        raise serializers.ValidationError("La secuencia está vacía.")
    if not DNA_PATTERN.match(seq):
        raise serializers.ValidationError("La secuencia solo puede contener A, T, C, G o N.")
    return seq
