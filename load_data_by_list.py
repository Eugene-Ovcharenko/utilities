import os
import shutil
import pandas as pd


def dataloader(
        datalist_path: str,
        export_dir: str,
) -> None:
    """
    Load data from a data list file and copy files to corresponding dataclass subdirectories
    in the export directory (corresponding to symbol in 'Dataset' column of datalist file).
    Generate an info file with class distribution.

    Args:
        datalist_path (str): The path to the data list file (Excel format like 'data/data_list_v1.xlsx').
        export_dir (str): The path to the export directory (like '/media/nii/SP PHD U3/dataset/markup_dataset').

    Returns:
        None
    """

    df = pd.read_excel(datalist_path)
    data_classes = df['Dataset'].value_counts()
    os.makedirs(export_dir, exist_ok=True)
    reminder = pd.Series({'remainder': df['Dataset'].isna().sum()})
    info = pd.concat([data_classes, reminder])
    info.to_excel(os.path.join(export_dir, 'info.xlsx'), index=True)
    print(info)

    for data_class in data_classes.index:
        print(data_class)
        export_dir_class = os.path.join(export_dir, data_class)
        os.makedirs(export_dir_class, exist_ok=True)

        files = df[df['Dataset'] == data_class]['Filename']
        for file in files:
            dirpath = df[df['Filename'] == file]['Path'].iloc[0]
            filepath = os.path.join(dirpath, file)
            shutil.copy(filepath, export_dir_class)
            print(f"File '{file}' copied to '{export_dir_class}'.")


if __name__ == '__main__':
    datalist_path = 'data/data_list_v1.xlsx'
    export_dir = '/media/nii/SP PHD U3/dataset/markup_dataset'

    dataloader(datalist_path, export_dir)
