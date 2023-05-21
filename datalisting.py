import os
import pandas as pd


def datalisting(
        path: str,
        file_types: tuple,
) -> None:
    """
    Create a dataframe of file paths and filenames that match the given file types
    in the specified directory and its subdirectories. Saves the dataframe to the 'data_list.xlsx'.

    Args:
        path (str): The root directory path to search for files, example: ('.jpeg', '.jpg', '.png', '.bmp', '.gif').
        file_types (tuple): A tuple of file extensions or types to include in the listing.

    Returns:
        None
    """

    df = pd.DataFrame(columns=['Path', 'Filename'])
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if any(file.endswith(file_types) for file in os.listdir(dir_path)):
                for file in os.listdir(dir_path):
                    if file.endswith(file_types):
                        row_add = pd.DataFrame({'Path': dir_path, 'Filename': file}, index=[0])
                        df = pd.concat([df, row_add], axis=0, ignore_index=True)
                df['Slide_number'] = df['Filename'].str.extract(r'slide_(\d+)_res').astype(int)
                df.sort_values(by=['Path', 'Slide_number'], inplace=True)
    print(df)
    path = os.path.join(path, 'data_list.xlsx')
    df['Dataset'] = None
    df.to_excel(path, index=False)


if __name__ == '__main__':
    file_types = ('.jpeg', '.jpg', '.png', '.bmp', '.gif')
    dir_path = '/media/nii/SP PHD U3/dataset/sliced'
    datalisting(dir_path, file_types)
