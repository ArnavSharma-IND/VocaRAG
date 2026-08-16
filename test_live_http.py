import httpx

r_debug = httpx.get('http://127.0.0.1:8000/api/debug/rag')
print('DEBUG RAG:', r_debug.json())

r_docs = httpx.get('http://127.0.0.1:8000/api/documents')
print('DOCS COUNT:', len(r_docs.json()))
for d in r_docs.json():
    print(f"  - {d['name']}: {d.get('category_badge', 'SAMPLE')} ({d['chunks_count']} chunks)")

r1 = httpx.post('http://127.0.0.1:8000/api/ask', json={'query': 'What is photosynthesis?'})
print('ASK Photosynthesis:', r1.json()['grounded'], r1.json()['sources'][0]['doc_name'], r1.json()['sources'][0]['category_label'])

r2 = httpx.post('http://127.0.0.1:8000/api/ask', json={'query': 'What is the refund policy?'})
print('ASK Refund Policy:', r2.json()['grounded'], r2.json()['sources'][0]['doc_name'], r2.json()['sources'][0]['category_label'])

r3 = httpx.post('http://127.0.0.1:8000/api/ask', json={'query': 'What is the population of a fictional planet called Xylon-9?'})
print('ASK Unknown Xylon-9: grounded=', r3.json()['grounded'], 'abstained=', r3.json()['abstained'])
