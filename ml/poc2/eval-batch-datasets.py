df = pd.read_csv("csv-on-gcs-training-data.csv")
df = df.rename(columns={'content_text':'texts'})
texts = df[['texts']]
texts.to_json('batch-predict.jsonl', orient='records', lines=True)