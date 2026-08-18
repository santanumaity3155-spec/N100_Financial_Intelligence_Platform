from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

print("--- Testing 1. GET /api/v1/companies ---")
res = client.get("/api/v1/companies")
print("Status:", res.status_code)
comps = res.json()
print("Count:", len(comps))
if len(comps) > 0:
    print("First comp:", comps[0])

print("\n--- Testing Sector filter: GET /api/v1/companies?sector=IT ---")
res = client.get("/api/v1/companies?sector=IT")
print("Status:", res.status_code, "Count:", len(res.json()))

print("\n--- Testing Market Cap filter: GET /api/v1/companies?market_cap_category=Large Cap ---")
res = client.get("/api/v1/companies?market_cap_category=Large Cap")
print("Status:", res.status_code, "Count:", len(res.json()))

print("\n--- Testing Search filter: GET /api/v1/companies?search=tcs ---")
res = client.get("/api/v1/companies?search=tcs")
print("Status:", res.status_code, "Result:", res.json())

print("\n--- Testing 2. GET /api/v1/companies/TCS ---")
res = client.get("/api/v1/companies/TCS")
print("Status:", res.status_code)
print("Keys:", list(res.json().keys()) if res.status_code == 200 else res.json())

print("\n--- Testing GET /api/v1/companies/INVALIDTICKER ---")
res = client.get("/api/v1/companies/INVALIDTICKER")
print("Status:", res.status_code, "Detail:", res.json())

print("\n--- Testing 3. GET /api/v1/companies/TCS/pl ---")
res = client.get("/api/v1/companies/TCS/pl")
print("Status:", res.status_code, "Count:", len(res.json()))

print("\n--- Testing P&L year filter: GET /api/v1/companies/TCS/pl?from_year=2019-03&to_year=2024-03 ---")
res = client.get("/api/v1/companies/TCS/pl?from_year=2019-03&to_year=2024-03")
print("Status:", res.status_code, "Count:", len(res.json()))

print("\n--- Testing P&L invalid year format: GET /api/v1/companies/TCS/pl?from_year=invalid ---")
res = client.get("/api/v1/companies/TCS/pl?from_year=invalid")
print("Status:", res.status_code, "Detail:", res.json())

print("\n--- Testing P&L invalid range: GET /api/v1/companies/TCS/pl?from_year=2024&to_year=2020 ---")
res = client.get("/api/v1/companies/TCS/pl?from_year=2024&to_year=2020")
print("Status:", res.status_code, "Detail:", res.json())

print("\n--- Testing 4. GET /api/v1/companies/TCS/bs ---")
res = client.get("/api/v1/companies/TCS/bs")
print("Status:", res.status_code, "Count:", len(res.json()))

print("\n--- Testing 5. GET /api/v1/companies/TCS/cashflow ---")
res = client.get("/api/v1/companies/TCS/cashflow")
print("Status:", res.status_code, "Count:", len(res.json()))

print("\n--- Testing 6. GET /api/v1/companies/TCS/ratios ---")
res = client.get("/api/v1/companies/TCS/ratios")
print("Status:", res.status_code, "Count:", len(res.json()))

print("\n--- Testing 7. GET /api/v1/companies/TCS/tearsheet ---")
res = client.get("/api/v1/companies/TCS/tearsheet")
print("Status:", res.status_code, "Content-Type:", res.headers.get("content-type"), "Length:", len(res.content))

print("\n--- Testing Tearsheet path traversal: GET /api/v1/companies/..%2F..%2Fetc%2Fpasswd/tearsheet ---")
res = client.get("/api/v1/companies/..%2F..%2Fetc%2Fpasswd/tearsheet")
print("Status:", res.status_code, "Detail:", res.json())

