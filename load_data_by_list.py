import os
import re
import shutil
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


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

    df['file_dir'] = df['Path'].str.split('/').str[-1].str.extract(r'(\d{3}_sheep_.{2})')
    df['map'] = df['Dataset'].notna().astype(int)

    # heatmap
    df_map = df.pivot("Slide_number", "file_dir", "map")
    fig = plt.figure(facecolor=(0.7, 0.7, 0.7), figsize=(20, 5))
    ax = sns.heatmap(df_map, cmap='winter', cbar=False)
    ax.set_facecolor((0.1, 0.1, 0.1))
    ax.invert_yaxis()
    x_ticks = range(len(df_map.columns))
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(df_map.columns, rotation=90, fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(export_dir, 'dataset_heatmap.png'), dpi=300, bbox_inches='tight')

    # del NaN rows
    df = df[df['map'] == 1]
    df.to_excel(os.path.join(export_dir, 'df_info.xlsx'), index=True)

    for data_class in data_classes.index:
        print(data_class)
        export_dir_class = os.path.join(export_dir, data_class)
        os.makedirs(export_dir_class, exist_ok=True)

        files = df[df['Dataset'] == data_class]['Filename']

        for id in files.index:
            # old file path
            dataset_path = df.loc[id, 'Path']
            file = df.loc[id, 'Filename']
            dataset_file_path = os.path.join(dataset_path, file)

            # new file path
            file_pref = df.loc[id, 'file_dir']
            file_num = int(re.findall(r'slide_(\d+)_res', file)[0])
            file_type = file.split('.')[-1]
            nfile = f'{file_pref}_slide_{file_num :04d}.{file_type}'
            export_dir_file_path = os.path.join(export_dir_class, nfile)

            shutil.copy(dataset_file_path, export_dir_file_path)
            print(f"File '{nfile}' copied to '{export_dir_class}'.")


if __name__ == '__main__':
    datalist_path = 'data/data_list_v1.xlsx'
    export_dir = '/media/nii/SP PHD U3/dataset/markup_dataset'

    dataloader(datalist_path, export_dir)
