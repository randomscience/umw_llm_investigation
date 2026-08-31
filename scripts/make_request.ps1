curl.exe -X POST "http://localhost:8000/v1/rag" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer debug-token" `
  -d "@scripts/request.json"
