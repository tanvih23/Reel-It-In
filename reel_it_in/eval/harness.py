"""Precision/recall harness for the safety question set. Owner: Kirtika."""

# TODO: run the labeled clips in eval/clips through safety.analyze
# TODO: score against the labels and write docs/eval-results.md
import json
import os
from reel_it_in.vision.safety import analyze

import os
labels_path = os.path.join(os.path.dirname(__file__), "labels.json")
with open(labels_path) as f:
    labels = json.load(f)

true_positives = 0
false_positives = 0
false_negatives = 0
true_negatives = 0

for label in labels:
    clip_path = os.path.join(os.path.dirname(__file__), "clips", label["clip"])
    predictions = analyze(clip_path)

    matching_prediction = None
    for prediction in predictions:
        if prediction["question"] == label["question"]:
            matching_prediction = prediction
            break

    if matching_prediction is None:
        print("No prediction found for:", label["question"], "in", label["clip"])
        continue
    

    predicted = matching_prediction["match"]
    expected = label["expected_match"]

    if predicted and expected:
        true_positives += 1
    elif predicted and not expected:
        false_positives += 1
    elif not predicted and expected:
        false_negatives += 1
    else:
        true_negatives += 1

print("True Positives:", true_positives)
print("False Positives:", false_positives)
print("False Negatives:", false_negatives)
print("True Negatives:", true_negatives)

precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0

print("Precision:", precision)
print("Recall:", recall)