import json
import msgpack

dataset = json.load(open("dataset/dataset.json"))
print(dataset.keys())
mpack = {
    'folder_path': "dataset",
    'size': dataset["Length"],
    'names': dataset["Filenames"],
    'vectors': dataset["Vectors"],
}
msgpack.dump(mpack, open("dataset/dataset.mpack", "wb"))