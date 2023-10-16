import os
import re
import shutil
import pandas as pd
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)


def universal_renamer(
        folder_path: str,
        original_file_regex: str,
        new_file_regex: str,
) -> None:
    '''
    Renames files in a folder and logs the changes.
    This function walks through the specified folder and its subdirectories,
    matches files based on the provided regular expression pattern, renames
    the files using the replacement pattern, and logs the changes in an Excel
    file named 'changelogger.xlsx'.

    Args:
        folder_path (str): Path to the folder containing files to rename.
        original_file_regex (str): Regular expression pattern for matching original file names.
        new_file_regex (str): Regular expression replacement pattern for new file names.
    '''
    changelogger = pd.DataFrame(columns=['Original_filename', 'Modified_filename'])
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if re.match(original_file_regex, file):
                new_file = re.sub(original_file_regex, new_file_regex, file)
                old_path = os.path.join(root, file)
                new_path = os.path.join(root, new_file)
                print(f'Renaming: {old_path} -> {new_path}')
                os.rename(old_path, new_path)
                print(old_path, new_path)
                changelogger = changelogger.append(
                    pd.Series({'Original_filename': old_path, 'Modified_filename': new_path}),
                    ignore_index=True
                )

    path = os.path.join(folder_path, 'changelogger.xlsx')
    changelogger.to_excel(path, index=False)


if __name__ == '__main__':
    folder_path = '/media/nii/LNB 1 5TB/dataset/markup_dataset_max_quality_v3.2'
    original_file_regex = r'(\d+)_sheep_(?:\w+)_slide_(\d+)\.(\w+)'
    new_file_regex = r'\1_\2.\3'

    universal_renamer(
        folder_path,
        original_file_regex,
        new_file_regex
    )
