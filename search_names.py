import re

text = "A stranger arrives, a name is recorded in the ledger and goes to the room, a death leaves behind more questions than answers somewhere between the lines lies another name. Trace the historical records to uncover the identity concealed in the case."

clean = "".join([c.lower() for c in text if c.isalpha()])
print("Length of clean letters:", len(clean))

# Common first names
names = [
    "artemus", "ogletree", "owen", "roland", "eugene", "scott", "donald", "hadland",
    "kate", "morgan", "lottie", "bernard", "barnard", "katie", "farmer", "logan",
    "lyle", "stevik", "fairgate", "jennifer", "isdal", "mary", "anderson", "alison",
    "lowell", "elisa", "lam", "tamam", "shud", "carl", "webb", "somerton", "robin",
    "peter", "bergmann", "george", "edward", "charles", "louise", "don", "jordan",
    "greg", "fleniken", "albert", "dekker", "kimberly", "mclean", "lori", "ruff",
    "joseph", "chandler", "nichols", "robert"
]

print("--- Substring search in clean text ---")
for n in names:
    idx = clean.find(n)
    if idx != -1:
        print(f"Found {n} at {idx}")

print("\n--- Word-level substrings (spanning across word boundaries) ---")
words = text.split()
joined_words = " ".join(words).lower()
for n in names:
    if n in joined_words:
        print(f"Found {n} in words: {joined_words[joined_words.find(n)-10:joined_words.find(n)+len(n)+10]}")

print("\n--- Skip letters (ELS) ---")
for step in range(2, 30):
    for offset in range(step):
        s = clean[offset::step]
        for n in names:
            if n in s:
                print(f"Found {n} with step {step}, offset {offset}")
