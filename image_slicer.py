import time
import logging
import os
from typing import List

import hydra
import json
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import openslide
from openslide import OpenSlide
from joblib import Parallel, parallel_backend, delayed
from omegaconf import DictConfig

os.makedirs('logs', exist_ok=True)
logging.basicConfig(filename='logs/logfile.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s'
                    )


class SlideGrid:
    num: int
    boundary_box: tuple
    boundary_box_small: tuple
    flag: int

    def __init__(self, num, boundary_box, boundary_box_small, flag):
        self.num = num
        self.boundary_box = boundary_box
        self.boundary_box_small = boundary_box_small
        self.flag = flag


def get_mrxs_files(
        data_folder: str
) -> list:
    """
    Retrieves a list of .mrxs files from the specified data folder.

    Args:
        data_folder (str): The path to the data folder.

    Returns:
        list: A list of .mrxs file paths.

    """
    mrxs_files = []
    for root, dirs, files in os.walk(data_folder):
        for file in files:
            if file.endswith('.mrxs'):
                file_path = os.path.join(root, file)
                mrxs_files.append(file_path)
    return mrxs_files


def detect_empty_slide(
        slide: OpenSlide,
        threshold_alpha: float = 0.5,
        threshold_red_blue_ratio: float = 0.99,
) -> int:
    """
    Detects if a slide (OpenSlide) is empty based on thresholds.

    Args:
        slide (OpenSlide): The OpenSlide object representing the slide.
        threshold_alpha (float, optional): The threshold for alpha pixels ratio.
        threshold_red_blue_ratio (float, optional): The threshold for red-blue pixels ratio.

    Returns:
        int: Flag indicating if the slide is empty (1) or not (0).

    """
    slide_np = np.array(slide.convert("RGBA"))
    red_pixels_count = np.sum(slide_np[:, :, 0])
    blue_pixels_count = np.sum(slide_np[:, :, 2])
    alpha_pixels_ratio = np.count_nonzero(slide_np[:, :, 3]) / slide_np[:, :, 3].size

    if alpha_pixels_ratio > threshold_alpha:
        if blue_pixels_count / (red_pixels_count+1) > threshold_red_blue_ratio:
            flag = 0
        else:
            flag = 1
    else:
        flag = 0
    return flag

def draw_gridmap(
        mrxs_file: str,
        slide_image: Image,
        slide_grids: List[SlideGrid],
        image_width: int,
        image_height: int,
        export_folder: str,
) -> str:
    """
    Draws grid map on the slide image and saves it as a PNG image file along with a corresponding JSON file.

    Args:
        mrxs_file (str): The path of the *.mrxs file.
        slide_image (Image): The slide image as a PIL Image object.
        slide_grids (List[SlideGrid]): A list of SlideGrid objects containing grid information.
        image_width (int): The width of the image grid.
        image_height (int): The height of the image grid.
        export_folder (str): The path of the folder to save the grid map image and JSON file.

    Returns:
        str: The path of the saved JSON file.

    """
    draw = ImageDraw.Draw(slide_image)
    for slide_grid in slide_grids:
        if slide_grid.flag == 1:
            draw.rectangle(slide_grid.boundary_box_small, outline='blue', width=2)
            text_size = int((slide_grid.boundary_box_small[2] - slide_grid.boundary_box_small[0]) / 5)
            try:
                font = ImageFont.truetype('arial.ttf', text_size)
            except OSError:
                font = ImageFont.truetype('Ubuntu-B.ttf', text_size)
            draw.text(
                (int(slide_grid.boundary_box_small[0] + text_size),
                 int(slide_grid.boundary_box_small[1]) + text_size),
                f"{slide_grid.num}", fill="blue", font=font)
    # Crop Image
    slide_image_np = np.array(slide_image)
    slide_image_cropped = slide_image_np[
                          slide_grids[0].boundary_box_small[1]:int(slide_grid.boundary_box_small[3] + 1),
                          slide_grids[0].boundary_box_small[0]:int(slide_grid.boundary_box_small[2] + 1),
                          :]  # use boundary_box_small last values from cycle
    # Save Image
    folder_name = os.path.dirname(mrxs_file).split('/')[-1]
    folder_name = folder_name.replace(' ', '_')
    filename = f'map_{folder_name}_{image_width}x{image_height}.png'
    filename = os.path.join(export_folder, filename)
    Image.fromarray(slide_image_cropped).save(filename)
    logging.info(f'Gridmap image saved: {filename}')
    print(f'Gridmap image saved: {filename}')
    # Save JSON
    filename = f'map_{folder_name}_{image_width}x{image_height}.json'
    filename = os.path.join(export_folder, filename)
    slide_grids_dict = [vars(sg) for sg in slide_grids]
    json_str = json.dumps(slide_grids_dict)
    with open(filename, 'w') as f:
        f.write(json_str)
    return filename

def export_region_images(
        slide_grid: SlideGrid,
        slide: OpenSlide,
        mrxs_file: str,
        export_format: str,
        image_width: int,
        image_height: int,
        export_folder: str,
) -> None:
    """
    Export region images based on the specified slide grid.

    Args:
        slide_grid (SlideGrid): The slide grid object.
        slide (OpenSlide): The OpenSlide object representing the slide.
        mrxs_file (str): The path of the *.mrxs file.
        export_format (str): The export format for the region images (e.g., 'png', 'jpg', 'jpeg').
        image_width (int): The width of the exported images.
        image_height (int): The height of the exported images.
        export_folder (str): The path of the folder to save the exported region images.

    Returns:
        None

    """
    if slide_grid.flag == 1:
        max_resolution_level = slide.get_best_level_for_downsample(1.0)
        slide_image_max_res = slide.read_region(
            (slide_grid.boundary_box[0], slide_grid.boundary_box[1]),
            max_resolution_level,
            (slide_grid.boundary_box[2] - slide_grid.boundary_box[0],
             slide_grid.boundary_box[3] - slide_grid.boundary_box[1]),
        )
        folder_name = os.path.dirname(mrxs_file).split('/')[-1].replace(' ', '_')
        folder_name = f'{folder_name}_{export_format}_{image_width}x{image_height}'
        filename = f'slide_{slide_grid.num}_res_{image_width}x{image_height}.{export_format}'
        path = os.path.join(export_folder, folder_name)
        os.makedirs(path, exist_ok=True)
        filename = os.path.join(path, filename)
        if export_format == 'png':
            slide_image_max_res.save(filename, optimize=False, dpi=(300, 300), compress_level=0)
        elif export_format == 'jpg' or export_format == 'jpeg':
            wb_slide = Image.new('RGB', slide_image_max_res.size, (255, 255, 255))
            wb_slide.paste(slide_image_max_res, mask=slide_image_max_res.split()[3])
            wb_slide.save(filename, quality=30)
        else:
            slide_image_max_res.save(filename)
        print(f'{filename}\t\t - saved')
        logging.info(f'{filename}\t\t - saved')


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
    return total_size / 1024 ** 2


@hydra.main(config_path='config', config_name='config', version_base=None)
def main(cfg: DictConfig):
    """
    Main function for processing slide images and exporting region images.
    It prepares a grid map (sized image_width * image_height) for each subfolder
    with *.mrxs files in the given path and saves the map image in the '\sliced' subfolder.
    If 'save_cut_images' is True, it exports each element of the slide grid
    in the highest possible quality to the 'export_format' file."

    Args:
        cfg: config/config.yaml: The configuration settings.
            - data_folder (str): The path to the data folder containing the slide images.
            - image_width (int): The width of each exported region image.
            - image_height (int): The height of each exported region image.
            - save_cut_images (bool): Flag indicating whether to save the cut region images.
            - export_format (str): The format to use for exporting the region images.

    Returns:
        None

    """
    data_folder = cfg.data_folder
    image_width = cfg.image_width
    image_height = cfg.image_height
    save_cut_images = cfg.save_cut_images
    export_format = cfg.export_format
    mrxs_files = get_mrxs_files(data_folder)

    parent_folder = os.path.dirname(os.path.abspath(data_folder))
    export_folder = os.path.join(parent_folder, 'sliced')
    os.makedirs(export_folder, exist_ok=True)

    mrxs_files.sort()
    report = pd.DataFrame(columns=['mrxs_file', 'json', 'folder_name', 'image_num', 'size'])
    for mrxs_file in mrxs_files:
        start_time = time.time()
        slide = openslide.open_slide(mrxs_file)
        num_levels = slide.level_count

        logging.info(f'-' * 70)
        logging.info(f'File: {mrxs_file}')
        logging.info(f'cutting image width: {image_width}, cutting image height {image_height}')
        logging.info(f'Number of levels: {num_levels}')
        print(mrxs_file)
        print(f'Number of levels:{num_levels}\nLevel dimensions: {slide.level_dimensions}')

        # define the work (non-empty) area
        zoom = 4
        level = num_levels - zoom  # 0 is the highest resolution, (num_levels - 1) - lowest
        slide_image = slide.read_region((0, 0), level, slide.level_dimensions[level])
        slide_image_np = np.array(slide_image)
        image_gray = Image.fromarray(slide_image_np).convert('L')
        work_area = image_gray.getbbox()

        # calculate the grid in best resolution
        max_resolution_level = slide.get_best_level_for_downsample(1.0)
        max_zoom = num_levels - max_resolution_level
        level = num_levels - zoom
        slide_image = slide.read_region((0, 0), level, slide.level_dimensions[level])
        work_area_max_res = tuple(cord * 2 ** (max_zoom - zoom) for cord in work_area)
        num_images_x = int((work_area_max_res[2] - work_area_max_res[0]) / image_width)
        num_images_y = int((work_area_max_res[3] - work_area_max_res[1]) / image_height)

        print(f'Max zoom (zoom = {max_zoom}) work area: {work_area_max_res}')
        print(f'Images grid number: {num_images_x + 1} x {num_images_y + 1}, '
              f'total {(num_images_x + 1) * (num_images_y + 1)} images')
        logging.info(f'Max zoom (zoom = {max_zoom}) work area: {work_area_max_res}')
        logging.info(f'Images grid number: {num_images_x + 1} x {num_images_y + 1}, '
                     f'total {(num_images_x + 1) * (num_images_y + 1)} images')

        # Crop the slide
        num = 0
        slide_grids = []
        for j in range(num_images_y + 1):
            for i in range(num_images_x + 1):

                # boundary box in a full resolution
                boundary_box = (
                    work_area_max_res[0] + image_width * i,
                    work_area_max_res[1] + image_height * j,
                    work_area_max_res[0] + image_width * (i + 1),
                    work_area_max_res[1] + image_height * (j + 1)
                )

                # boundary box in a preview resolution
                boundary_box_small = tuple(int(cord * 2 ** (zoom - max_zoom)) for cord in boundary_box)
                slide_bbsmall = slide.read_region(
                    (boundary_box[0], boundary_box[1]),
                    level,
                    (boundary_box_small[2] - boundary_box_small[0], boundary_box_small[3] - boundary_box_small[1])
                )

                # flag 1 if region is filled less threshold
                flag = detect_empty_slide(slide=slide_bbsmall)
                if flag == 1:
                    num = num + 1
                slide_grid = SlideGrid(num, boundary_box, boundary_box_small, flag)
                slide_grids.append(slide_grid)
        print(f'Total {num} non empty slides')
        logging.info(f'Total {num} non empty slides')

        # draw a Image grid
        filename = draw_gridmap(mrxs_file, slide_image, slide_grids, image_width, image_height, export_folder)
        time_ = time.time() - start_time
        logging.info(f'Time for the map drawing: {time_:.2f} s.')
        print(filename)
        # Save grid of regions as cut images
        if save_cut_images:
            with parallel_backend('threading', n_jobs=-1):
                results = [
                    delayed(export_region_images)(
                        slide_grid, slide, mrxs_file, export_format, image_width, image_height, export_folder
                    ) for slide_grid in slide_grids
                ]
                Parallel()(results)

            time_ = time.time() - start_time
            logging.info(f'Time for the cut image export: {time_:.2f} s.')

        #report
        folder_name = os.path.dirname(mrxs_file).split('/')[-1].replace(' ', '_')
        folder_name = f'{folder_name}_{export_format}_{image_width}x{image_height}'

        path = os.path.join(export_folder, folder_name)
        if os.path.exists(path):
            fsize = get_directory_size(path)
            fsize_mb = f'{fsize:.0f} Mb'
        else:
            fsize_mb = '-'
        image_num = sum([slide_grid.flag for slide_grid in slide_grids])
        report.loc[len(report)] = [mrxs_file, filename, folder_name, image_num, fsize_mb]
        path = os.path.join(export_folder, 'report.xlsx')
        report.to_excel(path, index=False)
        print(f'Total time: {time_:.2f} s.')

if __name__ == '__main__':
    main()
