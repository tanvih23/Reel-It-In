def analyze(chunk_path):
    print("Pretending to analyze:", chunk_path)
    return [
        {
            "question": "is anyone tightly surrounded",
            "match": True,
            "confidence": 0.82,
            "timestamp": 15
        },
        {
            "question": "is someone on the ground",
            "match": False,
            "confidence": 0.20,
            "timestamp": 15
        }
    ]
