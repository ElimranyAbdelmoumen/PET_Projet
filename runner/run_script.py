#!/usr/bin/env python3
"""
Wrapper d'exécution qui capture les résultats Python.
Exécute le script utilisateur et capture:
- stdout/stderr
- La dernière expression évaluée
- Les variables marquées avec # @output
- Les DataFrames et autres objets Python
"""
import sys
import io
import json
import traceback

def serialize_result(obj):
    """Convertit un objet Python en représentation affichable."""
    try:
        # Pandas DataFrame
        if hasattr(obj, 'to_string'):
            return {
                'type': 'dataframe',
                'shape': list(obj.shape) if hasattr(obj, 'shape') else None,
                'value': obj.to_string(max_rows=50, max_cols=20)
            }
        # Pandas Series
        elif hasattr(obj, 'to_frame'):
            return {
                'type': 'series',
                'shape': list(obj.shape) if hasattr(obj, 'shape') else None,
                'value': obj.to_string(max_rows=50)
            }
        # NumPy array
        elif hasattr(obj, 'tolist') and hasattr(obj, 'shape'):
            import numpy as np
            return {
                'type': 'ndarray',
                'shape': list(obj.shape),
                'dtype': str(obj.dtype),
                'value': str(obj) if obj.size <= 100 else f"Array shape {obj.shape}, dtype {obj.dtype}"
            }
        # Liste, dict, etc.
        elif isinstance(obj, (list, dict, tuple, set)):
            try:
                return {
                    'type': type(obj).__name__,
                    'value': json.dumps(obj, indent=2, default=str)[:5000]
                }
            except:
                return {'type': type(obj).__name__, 'value': str(obj)[:5000]}
        # Autres objets
        else:
            return {
                'type': type(obj).__name__,
                'value': str(obj)[:5000]
            }
    except Exception as e:
        return {'type': 'error', 'value': f"Cannot serialize: {e}"}


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_script.py <script.py>", file=sys.stderr)
        sys.exit(1)

    script_path = sys.argv[1]

    # Lire le script
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        print(f"Error reading script: {e}", file=sys.stderr)
        sys.exit(1)

    # Namespace d'exécution
    namespace = {
        '__name__': '__main__',
        '__file__': script_path,
    }

    # Capturer stdout
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()

    results = {
        'stdout': '',
        'stderr': '',
        'outputs': [],
        'error': None
    }

    try:
        sys.stdout = captured_stdout
        sys.stderr = captured_stderr

        # Exécuter le script
        exec(compile(code, script_path, 'exec'), namespace)

        # Chercher les variables marquées @output ou result/output/df
        output_vars = ['result', 'output', 'df', 'data', 'results']
        
        # Parser les commentaires @output
        for line in code.split('\n'):
            if '# @output' in line or '#@output' in line:
                var_name = line.split('=')[0].strip() if '=' in line else None
                if var_name and var_name.isidentifier():
                    output_vars.insert(0, var_name)

        # Collecter les outputs
        for var_name in output_vars:
            if var_name in namespace and not var_name.startswith('_'):
                obj = namespace[var_name]
                if obj is not None:
                    results['outputs'].append({
                        'name': var_name,
                        **serialize_result(obj)
                    })

    except Exception as e:
        results['error'] = {
            'type': type(e).__name__,
            'message': str(e),
            'traceback': traceback.format_exc()
        }

    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        results['stdout'] = captured_stdout.getvalue()
        results['stderr'] = captured_stderr.getvalue()

    # Afficher les résultats en JSON
    print("===STDOUT===")
    print(results['stdout'])
    
    if results['stderr']:
        print("===STDERR===", file=sys.stderr)
        print(results['stderr'], file=sys.stderr)

    if results['error']:
        print("===ERROR===", file=sys.stderr)
        print(results['error']['traceback'], file=sys.stderr)

    if results['outputs']:
        print("===OUTPUTS===")
        for out in results['outputs']:
            print(f"--- {out['name']} ({out['type']}) ---")
            print(out['value'])
            print()

    # Exit code
    sys.exit(1 if results['error'] else 0)


if __name__ == '__main__':
    main()
