
try:
    from src.schemas.claims import AgentClaims
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
