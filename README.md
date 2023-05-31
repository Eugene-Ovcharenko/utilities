# Utilities
This is a collection of utilities for processing a dataset. Currently, it includes the following tool:


## datalisting.py
Prepare a table of file paths and filenames that match the given file types in the specified 
directory and its subdirectories.

## image_slicer.py
The module for processing slide images and exporting region images. It prepares a grid map for each subfolder
with *.mrxs files in the given path and saves the map image and each element of the slide map(grid) in the highest 
possible quality.

## load_data_by_list.py
Load data from a data list file and copy files to corresponding dataclass subdirectories in the export directory.

## renamer.py
This tool is intended for renaming the dataset folders using regular expressions (regex). 
It can be used to automate the renaming process of a large number of folders in a dataset.
