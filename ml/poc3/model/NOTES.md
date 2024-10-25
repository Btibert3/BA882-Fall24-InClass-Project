To build it

docker build --no-cache -t model .

To run it

docker run -p 8080:8080 model

To test via curl

```
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{"instances": [["This is my AWS Bedrock Title"]]}'
```

```
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{"instances": [["This is my AWS Bedrock Title"], ["AWS Bedrock Agents are now GA"]]}'
```


For test in the console

{"instances": [["This is my AWS Bedrock Title"]]}
{"instances": [["This is my AWS Bedrock Title"], ["S3 is an amazing service"]]}