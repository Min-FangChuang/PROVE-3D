import os
from time import sleep

DIR = "./scene"
DIR_ALI = "./alignment"

SCAN_LIST_FILE = "./scannetv2_val.txt"


def run(cmd):
    print("[RUN]", cmd)
    os.system(cmd)
    sleep(0.5)

if __name__ == '__main__':
    scene_list = [x.strip() for x in open(SCAN_LIST_FILE, 'r')]
    for scan in scene_list:
        print(f"\n=== Downloading scene: {scan} ===")

        # 1. .sens (multi-view RGB/Depth/pose)
        run(f"echo y | python download-scannet.py -o {DIR} --id {scan} --type .sens")

        # 2. point cloud (mesh)
        run(f"python download-scannet.py -o {DIR_ALI} --id {scan} --type .txt")

