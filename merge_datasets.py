from pathlib import Path
import shutil

PROJECT = Path(r"C:\Users\ADMIN\.gemini\antigravity\scratch\wildlife_detection")
D1 = Path(r"C:\Users\ADMIN\Downloads\WildAnimal_Dataset1")
D2 = Path(r"C:\Users\ADMIN\Downloads\AnimalDetection_Dataset2")

OUT_IMG = PROJECT / "dataset" / "images"
OUT_LBL = PROJECT / "dataset" / "labels"

# Final 10-class mapping
# 0 Elephant
# 1 Tiger
# 2 Lion
# 3 Leopard
# 4 Bear
# 5 Deer
# 6 Giraffe
# 7 Zebra
# 8 Wolf
# 9 Rhinoceros

MAP_D1 = {
    0: 0,   # Elephant
    2: 6,   # Giraffe
    3: 4,   # bear
    5: 5,   # deer
    10: 2,  # lion
    12: 1,  # tiger
    14: 8,  # wolf
    15: 7,  # zebra
}

MAP_D2 = {
    0: 3,   # Leopard
    1: 1,   # Tiger
    2: 4,   # bear
    4: 5,   # deer
    5: 0,   # elephant
    6: 6,   # giraffe
    7: 2,   # lion
    9: 9,   # rhinoceros
    10: 7,  # zebra
}


def merge_dataset(source, mapping, prefix):
    total_images = 0
    total_labels = 0
    skipped = 0

    for split in ["train", "valid", "test"]:
        source_images = source / split / "images"
        source_labels = source / split / "labels"

        if not source_images.exists():
            print(f"[WARNING] Missing: {source_images}")
            continue

        out_split = "val" if split == "valid" else split

        out_images = OUT_IMG / out_split
        out_labels = OUT_LBL / out_split

        out_images.mkdir(parents=True, exist_ok=True)
        out_labels.mkdir(parents=True, exist_ok=True)

        for image in source_images.iterdir():
            if image.suffix.lower() not in [".jpg", ".jpeg", ".png", ".webp"]:
                continue

            label = source_labels / f"{image.stem}.txt"

            if not label.exists():
                skipped += 1
                continue

            new_lines = []

            with open(label, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()

                    if len(parts) != 5:
                        continue

                    old_class = int(parts[0])

                    # Keep only our required 10 animals
                    if old_class in mapping:
                        parts[0] = str(mapping[old_class])
                        new_lines.append(" ".join(parts))

            # Skip images containing no target animal
            if not new_lines:
                skipped += 1
                continue

            new_name = f"{prefix}_{image.name}"
            new_label_name = f"{prefix}_{image.stem}.txt"

            shutil.copy2(image, out_images / new_name)

            with open(out_labels / new_label_name, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines) + "\n")

            total_images += 1
            total_labels += len(new_lines)

    return total_images, total_labels, skipped


print("=" * 60)
print("MERGING WILDLIFE DATASETS")
print("=" * 60)

print("\n[1/2] Processing Dataset 1...")
a = merge_dataset(D1, MAP_D1, "D1")
print(f"Dataset 1 -> Images: {a[0]}, Objects: {a[1]}, Skipped: {a[2]}")

print("\n[2/2] Processing Dataset 2...")
b = merge_dataset(D2, MAP_D2, "D2")
print(f"Dataset 2 -> Images: {b[0]}, Objects: {b[1]}, Skipped: {b[2]}")

print("\n" + "=" * 60)
print("MERGE COMPLETE")
print("=" * 60)

print(f"Total Images : {a[0] + b[0]}")
print(f"Total Objects: {a[1] + b[1]}")
print(f"Skipped      : {a[2] + b[2]}")

print("\nFinal classes:")
classes = [
    "Elephant",
    "Tiger",
    "Lion",
    "Leopard",
    "Bear",
    "Deer",
    "Giraffe",
    "Zebra",
    "Wolf",
    "Rhinoceros",
]

for i, name in enumerate(classes):
    print(f"{i}: {name}")
