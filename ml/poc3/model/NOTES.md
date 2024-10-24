To test via curl

```
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{"instances": [["This is my AWS Bedrock Title"]]}'
```