
import os, pickle, itertools, glob, shutil

class Save():
    def __init__(self, dir):
        self.working_dir = dir
        
        self.dump_dir = os.path.join(self.working_dir, "dumps")
        os.makedirs(self.dump_dir)
        self.dump_number = 0
    
    def dump(self, data):
        with open(os.path.join(self.dump_dir, str(self.dump_number)), "wb") as file:
            pickle.dump(data, file)
        self.dump_number += 1

    def store(self, file_name):
        all_data = []
        for file_path in glob.glob("./" + self.dump_dir + "/*"):
            with open(file_path, "rb") as file:
                all_data += pickle.load(file)

        # 1つのファイルに格納
        with open(os.path.join(self.working_dir, file_name), "wb") as file:
            pickle.dump(all_data, file)

        shutil.rmtree(self.dump_dir)
        self.dump_number = 0
