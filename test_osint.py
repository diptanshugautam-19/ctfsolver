import re

desc = """A stranger arrives, a name is recorded in the ledger and goes to the room, a death leaves behind more questions than answers somewhere between the lines lies another name. Trace the historical records to uncover the identity concealed in the case. Things to uncover all lower case real_name_hair_colour_eye_colour_height_feet."""

# Check any substring that could be a name
words = re.findall(r"\b\w+\b", desc)
print("Words count:", len(words))

# Check for hidden names across words (e.g. joined text)
clean_text = re.sub(r'[^a-zA-Z]', '', desc.lower())
print("Clean text:", clean_text)

# Check if any famous names appear in clean_text
names = ["artemus", "ogletree", "owen", "roland", "eugene", "scott", "donald", "hadland", 
         "stevik", "lyle", "fairgate", "jennifer", "bergmann", "peter", "isdal", "tamam",
         "somerton", "carol", "anderson", "mary", "george", "john", "david", "william", "charles"]

for n in names:
    if n in clean_text:
        print(f"Found name: {n} in clean_text!")
