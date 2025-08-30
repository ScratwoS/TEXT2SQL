import sys
from .executor import run_pipeline

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m app.cli \"your question here\"")
        sys.exit(1)
    q = sys.argv[1]
    out = run_pipeline(q, synthesize=True)
    print("Intent:", out["intent"])
    print("SQL:", out["sql"])
    print("Columns:", out["columns"])
    print("Rows (first 5):", out["rows"][:5])
    print("Answer:", out.get("answer"))

if __name__ == "__main__":
    main()
