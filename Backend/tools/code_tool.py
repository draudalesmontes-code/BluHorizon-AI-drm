import sys
import io
import traceback


CODE_TOOL_DEFINITION = {
    "name": "execute_python",

    "description": (
        "Execute Python code and return the output. Use this to perform "
        "calculations, data analysis, string manipulation, or any task "
        "that benefits from writing and running code. "
        "Use print() to output the results you want returned."
    ),

    "input_schema": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Valid Python code to execute. Use print() to output results."
            }
        },
        "required": ["code"]
    }
}

def run_code(code: str) -> str:
    stdout_capture = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout_capture

    try:
        safe_builtins = {
            "print":     print,
            "len":       len,
            "range":     range,
            "list":      list,
            "dict":      dict,
            "set":       set,
            "tuple":     tuple,
            "int":       int,
            "float":     float,
            "str":       str,
            "bool":      bool,
            "abs":       abs,
            "min":       min,
            "max":       max,
            "sum":       sum,
            "round":     round,
            "sorted":    sorted,
            "enumerate": enumerate,
            "zip":       zip,
            "map":       map,
            "filter":    filter,
            "isinstance": isinstance,
        }

        exec(code, {"__builtins__": safe_builtins}, {})

        output = stdout_capture.getvalue()
        return output if output else "(Code ran successfully, no output printed)"

    except Exception:
        return f"Error:\n{traceback.format_exc()}"

    finally:
        sys.stdout = old_stdout
