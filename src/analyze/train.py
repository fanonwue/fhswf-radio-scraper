import re
import spacy
import random
import os
from pathlib import Path
from spacy.util import minibatch, compounding
from spacy.training.example import Example


def load_tagged_lines_from_folder(folder_path):
    pattern = re.compile(r"^\[SPEAKER_[0-9]+ \| [\d.]+-[\d.]+(?: \| tag:([a-z_]+))\] (.+)$")
    train_data = []

    folder = Path(folder_path)
    for file in folder.glob("*.txt"):
        with file.open("r", encoding="utf-8") as f:
            for line in f:
                match = pattern.match(line.strip())
                if match:
                    label, text = match.groups()
                    # Einträge mit dem Tag 'skip' ignorieren
                    if label == "skip":
                        continue
                    train_data.append((text.strip(), {"cats": {label: 1.0}}))
    return train_data


def train_classifier(train_data, model_path="models/text_classifier.spacy"):
    nlp = spacy.blank("de")
    textcat = nlp.add_pipe("textcat", last=True)

    labels = {label for _, d in train_data for label in d["cats"].keys()}
    for label in labels:
        textcat.add_label(label)

    optimizer = nlp.begin_training()

    examples = [Example.from_dict(nlp.make_doc(text), annotation) for text, annotation in train_data]

    for i in range(10):
        random.shuffle(examples)
        batches = minibatch(examples, size=compounding(4.0, 32.0, 1.001))
        for batch in batches:
            nlp.update(batch, sgd=optimizer)

    os.makedirs(Path(model_path).parent, exist_ok=True)
    nlp.to_disk(model_path)
    print(f"✅ Modell gespeichert unter: {model_path}")


def classify(text, model_path="models/text_classifier.spacy"):
    nlp = spacy.load(model_path)
    doc = nlp(text)
    return doc.cats


if __name__ == "__main__":
    folder = "data/swr3/labeled/"
    model_path = "data/models/text_classifier.spacy"

    train_data = load_tagged_lines_from_folder(folder)
    print(f"Geladene Trainingsbeispiele: {len(train_data)}")

    if train_data:
        train_classifier(train_data, model_path)

        test_weather = "Maximal 23 Grad heute Sonne, teilweise auch ein paar dichtere Quellwolken."
        print("Vorhersage 1:", classify(test_weather, model_path))

        test_traffic = "A6 Mannheim Richtung Heilbronn zwischen Dreieck Hockenheim und Wiesloch-Raunberg 2 Kilometer."
        print("Vorhersage 2:", classify(test_traffic, model_path))
    else:
        print("⚠️ Keine getaggten Zeilen gefunden. Bitte TAGs in den Dateien ergänzen.")
