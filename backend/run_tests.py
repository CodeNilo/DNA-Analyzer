#!/usr/bin/env python
"""
Script auxiliar para ejecutar tests del proyecto ADN-WebApp

Uso:
    python run_tests.py                    # Todos los tests
    python run_tests.py --unit             # Solo unitarios
    python run_tests.py --integration      # Solo integración
    python run_tests.py --coverage         # Con cobertura
    python run_tests.py --parallel         # En paralelo
    python run_tests.py --module sequences # Solo sequences_api
"""

import sys
import os
import argparse
import subprocess


def run_command(cmd):
    """Ejecuta un comando y muestra output en tiempo real"""
    print(f"\n🚀 Ejecutando: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description='Ejecutar tests del proyecto ADN-WebApp'
    )

    # Tipos de tests
    parser.add_argument('--unit', action='store_true',
                        help='Ejecutar solo pruebas unitarias')
    parser.add_argument('--integration', action='store_true',
                        help='Ejecutar solo pruebas de integración')
    parser.add_argument('--functional', action='store_true',
                        help='Ejecutar solo pruebas funcionales')
    parser.add_argument('--e2e', action='store_true',
                        help='Ejecutar solo pruebas E2E')
    parser.add_argument('--acceptance', action='store_true',
                        help='Ejecutar solo pruebas de aceptación')
    parser.add_argument('--security', action='store_true',
                        help='Ejecutar solo pruebas de seguridad')
    parser.add_argument('--performance', action='store_true',
                        help='Ejecutar solo pruebas de rendimiento')

    # Módulos
    parser.add_argument('--module', type=str, choices=['sequences', 'search', 'all'],
                        help='Módulo específico a testear')

    # Opciones
    parser.add_argument('--coverage', action='store_true',
                        help='Ejecutar con reporte de cobertura')
    parser.add_argument('--parallel', action='store_true',
                        help='Ejecutar tests en paralelo')
    parser.add_argument('--verbose', action='store_true',
                        help='Output verbose')
    parser.add_argument('--failfast', action='store_true',
                        help='Detener en el primer fallo')
    parser.add_argument('--lf', action='store_true',
                        help='Ejecutar solo tests que fallaron la última vez')
    parser.add_argument('--pdb', action='store_true',
                        help='Entrar en debugger al fallar')

    # Path específico
    parser.add_argument('path', nargs='?',
                        help='Path específico de test a ejecutar')

    args = parser.parse_args()

    # Construir comando pytest
    cmd = ['pytest']

    # Agregar markers
    markers = []
    if args.unit:
        markers.append('unit')
    if args.integration:
        markers.append('integration')
    if args.functional:
        markers.append('functional')
    if args.e2e:
        markers.append('e2e')
    if args.acceptance:
        markers.append('acceptance')
    if args.security:
        markers.append('security')
    if args.performance:
        markers.append('performance')

    if markers:
        cmd.extend(['-m', ' or '.join(markers)])

    # Agregar módulo
    if args.module:
        if args.module == 'sequences':
            cmd.append('sequences_api/tests/')
        elif args.module == 'search':
            cmd.append('search_api/tests/')
        # 'all' no agrega nada (ejecuta todo)

    # Agregar path específico
    if args.path:
        cmd.append(args.path)

    # Opciones
    if args.coverage:
        cmd.extend([
            '--cov=sequences_api',
            '--cov=search_api',
            '--cov-report=html',
            '--cov-report=term-missing'
        ])

    if args.parallel:
        cmd.extend(['-n', 'auto'])

    if args.verbose:
        cmd.append('-vv')

    if args.failfast:
        cmd.append('-x')

    if args.lf:
        cmd.append('--lf')

    if args.pdb:
        cmd.append('--pdb')

    # Ejecutar
    exit_code = run_command(cmd)

    # Mensaje final
    if exit_code == 0:
        print("\n✅ Todos los tests pasaron correctamente!\n")
    else:
        print(f"\n❌ Tests fallaron con código {exit_code}\n")

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
