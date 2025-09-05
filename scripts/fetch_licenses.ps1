$proj = Split-Path -Parent $PSScriptRoot
Push-Location $proj
python - <<'PY'
from app.core.licenses import fetch_all_known_licenses
st = fetch_all_known_licenses()
for k,v in st.items():
    print(f"{k}: {v}")
print("Cached under .\\licenses\\")
PY
Pop-Location
