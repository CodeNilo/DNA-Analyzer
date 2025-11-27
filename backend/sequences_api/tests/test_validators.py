"""
Pruebas unitarias para validators.py

Cubre:
- normalize_sequence
- validate_dna_sequence
- Validación de caracteres permitidos
- Manejo de casos edge (vacío, None, etc.)
"""

from django.test import TestCase
from rest_framework.serializers import ValidationError

from sequences_api.validators import normalize_sequence, validate_dna_sequence


class NormalizeSequenceTests(TestCase):
    """Pruebas para la función normalize_sequence"""

    def test_converts_to_uppercase(self):
        """Debe convertir secuencias a mayúsculas"""
        result = normalize_sequence("atcg")
        self.assertEqual(result, "ATCG")

    def test_removes_whitespace(self):
        """Debe eliminar espacios en blanco"""
        result = normalize_sequence("AT CG")
        self.assertEqual(result, "ATCG")

    def test_removes_newlines(self):
        """Debe eliminar saltos de línea"""
        result = normalize_sequence("AT\nCG\n")
        self.assertEqual(result, "ATCG")

    def test_removes_tabs(self):
        """Debe eliminar tabulaciones"""
        result = normalize_sequence("AT\tCG")
        self.assertEqual(result, "ATCG")

    def test_handles_mixed_case(self):
        """Debe manejar mayúsculas y minúsculas mezcladas"""
        result = normalize_sequence("AtCgN")
        self.assertEqual(result, "ATCGN")

    def test_handles_empty_string(self):
        """Debe manejar cadena vacía"""
        result = normalize_sequence("")
        self.assertEqual(result, "")

    def test_handles_none(self):
        """Debe manejar None devolviendo cadena vacía"""
        result = normalize_sequence(None)
        self.assertEqual(result, "")

    def test_handles_only_whitespace(self):
        """Debe manejar cadenas que solo contienen espacios"""
        result = normalize_sequence("   \n\t  ")
        self.assertEqual(result, "")

    def test_complex_sequence(self):
        """Debe procesar secuencias complejas con múltiples espacios"""
        input_seq = "at cg\n\naa tt\t\tgg cc"
        result = normalize_sequence(input_seq)
        self.assertEqual(result, "ATCGAATTGGCC")


class ValidateDNASequenceTests(TestCase):
    """Pruebas para la función validate_dna_sequence"""

    def test_valid_sequence_uppercase(self):
        """Debe aceptar secuencia válida en mayúsculas"""
        seq = "ATCG"
        result = validate_dna_sequence(seq)
        self.assertEqual(result, "ATCG")

    def test_valid_sequence_with_n(self):
        """Debe aceptar secuencia con N (nucleótido desconocido)"""
        seq = "ATCGNATCG"
        result = validate_dna_sequence(seq)
        self.assertEqual(result, "ATCGNATCG")

    def test_valid_long_sequence(self):
        """Debe aceptar secuencias largas válidas"""
        seq = "ATCG" * 1000
        result = validate_dna_sequence(seq)
        self.assertEqual(result, seq)

    def test_rejects_empty_sequence(self):
        """Debe rechazar secuencia vacía"""
        with self.assertRaises(ValidationError) as context:
            validate_dna_sequence("")
        self.assertIn("vacía", str(context.exception))

    def test_rejects_invalid_characters_numbers(self):
        """Debe rechazar secuencias con números"""
        with self.assertRaises(ValidationError) as context:
            validate_dna_sequence("ATCG123")
        self.assertIn("solo puede contener", str(context.exception))

    def test_rejects_invalid_characters_symbols(self):
        """Debe rechazar secuencias con símbolos"""
        with self.assertRaises(ValidationError) as context:
            validate_dna_sequence("ATCG@#$")
        self.assertIn("solo puede contener", str(context.exception))

    def test_rejects_lowercase(self):
        """Debe rechazar minúsculas (debe normalizarse antes)"""
        with self.assertRaises(ValidationError) as context:
            validate_dna_sequence("atcg")
        self.assertIn("solo puede contener", str(context.exception))

    def test_rejects_spaces(self):
        """Debe rechazar espacios (debe normalizarse antes)"""
        with self.assertRaises(ValidationError) as context:
            validate_dna_sequence("AT CG")
        self.assertIn("solo puede contener", str(context.exception))

    def test_rejects_other_letters(self):
        """Debe rechazar otras letras no válidas"""
        with self.assertRaises(ValidationError) as context:
            validate_dna_sequence("ATCGXYZ")
        self.assertIn("solo puede contener", str(context.exception))


class IntegratedValidationTests(TestCase):
    """Pruebas de normalización + validación juntas"""

    def test_normalize_then_validate_success(self):
        """Pipeline completo: normalizar y luego validar"""
        raw = "at cg\naa tt"
        normalized = normalize_sequence(raw)
        validated = validate_dna_sequence(normalized)
        self.assertEqual(validated, "ATCGAATT")

    def test_normalize_then_validate_with_n(self):
        """Pipeline con N"""
        raw = "at n cg"
        normalized = normalize_sequence(raw)
        validated = validate_dna_sequence(normalized)
        self.assertEqual(validated, "ATNCG")

    def test_normalize_then_validate_fails(self):
        """Pipeline que falla después de normalización"""
        raw = "at cg 123"
        normalized = normalize_sequence(raw)
        with self.assertRaises(ValidationError):
            validate_dna_sequence(normalized)
