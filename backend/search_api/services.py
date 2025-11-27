import logging
import time
from typing import Dict, List

import grpc
from django.conf import settings

from sequences_api.validators import normalize_sequence, validate_dna_sequence
from .grpc_client import get_grpc_client

log = logging.getLogger(__name__)


def _find_matches(sequence: str, pattern: str, allow_overlapping: bool = True) -> List[Dict]:
    """
    Búsqueda naive para etapa inicial (sin microservicio C++).
    Devuelve lista de dicts con posición y contexto.
    """
    matches = []
    start = 0
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


def run_grpc_search(sequence: str, pattern: str, allow_overlapping: bool = True) -> Dict:
    """
    Ejecuta búsqueda vía microservicio gRPC (C++).
    """
    normalized_pattern = normalize_sequence(pattern)
    validated_pattern = validate_dna_sequence(normalized_pattern)

    client = get_grpc_client()
    log.info("Invocando gRPC a %s con allow_overlapping=%s", client.address, allow_overlapping)
    resp = client.search(sequence=sequence, pattern=validated_pattern, allow_overlapping=allow_overlapping)

    matches = []
    for m in resp.matches:
        matches.append({
            "position": m.position,
            "context_before": m.context_before,
            "context_after": m.context_after,
        })

    return {
        "pattern": validated_pattern,
        "total_matches": resp.total_matches or len(matches),
        "search_time_ms": resp.search_time_ms,
        "matches": matches,
        "algorithm_used": resp.algorithm_used or "grpc",
    }


def run_search(sequence: str, pattern: str, allow_overlapping: bool = True) -> Dict:
    """
    Orquesta la búsqueda usando gRPC si está habilitado, con fallback local.
    """
    use_grpc = getattr(settings, "USE_GRPC_SEARCH", False)
    if not use_grpc:
        return run_local_search(sequence, pattern, allow_overlapping)

    try:
        return run_grpc_search(sequence, pattern, allow_overlapping)
    except grpc.RpcError as exc:
        log.error("Fallo gRPC (%s). Usando fallback local.", exc)
        return run_local_search(sequence, pattern, allow_overlapping)
