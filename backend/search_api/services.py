import time
from typing import List, Dict

from sequences_api.validators import normalize_sequence, validate_dna_sequence


def _find_matches(sequence: str, pattern: str, allow_overlapping: bool = True, max_matches: int = 100000) -> List[Dict]:
    """
    Búsqueda naive para etapa inicial (sin microservicio C++).
    Devuelve lista de dicts con posición y contexto.
    """
    matches = []
    start = 0
    seq_len = len(sequence)
    pat_len = len(pattern)

    while True:
        idx = sequence.find(pattern, start)
        if idx == -1:
            break

        context_before = sequence[max(0, idx - 10):idx]
        context_after = sequence[idx + pat_len: idx + pat_len + 10]

        matches.append({
            "position": idx,
            "context_before": context_before,
            "context_after": context_after,
        })

        if len(matches) >= max_matches:
            break

        # Modo solapado vs directo
        start = idx + 1 if allow_overlapping else idx + pat_len

    return matches


def run_local_search(sequence: str, pattern: str, allow_overlapping: bool = True) -> Dict:
    """
    Ejecuta búsqueda local usando algoritmo simple.
    Retorna dict con métricas y matches.
    """
    normalized_pattern = normalize_sequence(pattern)
    validated_pattern = validate_dna_sequence(normalized_pattern)

    if len(validated_pattern) > 1000:
        raise ValueError("El patrón es demasiado largo (máximo 1000 caracteres).")

    t0 = time.perf_counter()
    matches = _find_matches(sequence, validated_pattern, allow_overlapping)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    return {
        "pattern": validated_pattern,
        "total_matches": len(matches),
        "search_time_ms": elapsed_ms,
        "matches": matches,
        "algorithm_used": "naive-local",
    }
