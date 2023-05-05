import os
import re
import pandas as pd


def get_directory_size(
        path: str
) -> float:
    total_size = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total_size += entry.stat().st_size
            elif entry.is_dir():
                total_size += get_directory_size(entry.path)
    return total_size / 1024


path = '/media/nii/SP PHD U3/dataset/source'

df = pd.DataFrame(columns=['new_name', 'original_name', 'size', 'path'])
for i, folder in enumerate(os.listdir(path)):
    if os.path.isdir(os.path.join(path, folder)):
        fsize_mb = get_directory_size(os.path.join(path, folder))
        fsize_mb = f'{fsize_mb:.0f} Mb'

        fname = re.search(r'sheep\s+(\d+)', folder) or re.search(r'овца\s+(\d+)', folder)
        if fname:
            sheep = f'sheep_{fname.group(1):02d}'
        else:
            sheep = 'sheep_NA'

        new_name = f'{i + 1:03d}_{sheep}'
        old_name_path = os.path.join(path, folder)
        new_name_path = os.path.join(path, new_name)
        os.rename(old_name_path, new_name_path)
        df.loc[i] = [new_name, folder, fsize_mb, path]

path = os.path.join(path, 'folder_list.xlsx')
df.to_excel(path, index=False)
