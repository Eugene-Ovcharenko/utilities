import os
import re
import pandas as pd

pd.options.mode.chained_assignment = None


def get_directory_size(
        path: str
) -> float:
    """
    Calculate the total size of a directory and its contents in Mb.

    Args:
        path (str): The path to the directory.

    Returns:
        float: The total size of the directory and its contents in Mb.
    """

    total_size = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total_size += entry.stat().st_size
            elif entry.is_dir():
                total_size += get_directory_size(entry.path)
    return total_size / 1024 / 1024


def renamer(
        path: str,
) -> None:
    """
    Rename folders in the specified directory based on a specific pattern.
    Creates a dataframe with the new names, original names, sizes, and paths.
    Renames the folders and saves the dataframe to the 'folder_list.xlsx'.

    Args:
        path (str): The root directory path where the folders are located.

    Returns:
        None
    """

    df = pd.DataFrame(columns=['new_name', 'original_name', 'size', 'path'])
    for i, folder in enumerate(os.listdir(path)):
        if os.path.isdir(os.path.join(path, folder)):
            fsize_mb = get_directory_size(os.path.join(path, folder))
            fsize_mb = f'{fsize_mb:.0f} Mb'

            fname = re.search(r'sheep\s*(\d+)', folder) or re.search(r'овца\s*(\d+)', folder)
            if fname:
                sheep = f'sheep_{int(fname.group(1)):02d}'
            else:
                sheep = 'sheep_NA'

            df.loc[i] = [sheep, folder, fsize_mb, path]
    df = df.sort_values(by=['new_name']).reset_index(drop=True)

    for i, row in df.iterrows():
        new_name = f'{(i + 1):03d}_{row.new_name}'
        df['new_name'].loc[i] = new_name

        old_name_path = os.path.join(row.path, row.original_name)
        new_name_path = os.path.join(row.path, row.new_name)
        os.rename(old_name_path, new_name_path)
    path = os.path.join(path, 'folder_list.xlsx')
    df.to_excel(path, index=False)


if __name__ == '__main__':
    path = '/media/nii/SP PHD U3/test/source'
    renamer(path=path)
