import os
import json

def gather_datas():
    content = ""
    
    for name in os.listdir("datas"):
        if os.path.isfile(os.path.join("datas", name)):
            with open(os.path.join("datas", name), "r", encoding="utf-8") as f:
                data = json.load(f)

                for key in data.keys():
                    content += data[key]["content"] + "\n"

    return content