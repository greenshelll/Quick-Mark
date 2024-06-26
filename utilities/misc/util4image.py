import os
import cv2
import numpy as np

import math

"""def _extract_rar(archive_path, extract_dir):
    # Extract the RAR archive to the specified directory
    patoolib.extract_archive(archive_path, outdir=extract_dir)
"""
def _have_content(directory):
    # Get a list of all files and directories in the specified directory
    contents = os.listdir(directory)
    
    # Count the number of items (files and directories)
    num_items = len(contents)

    if num_items>0:
        return True
    else:
        return False
    
"""def extract_all_images():
    _extract_rar('assets/idtf_img.rar','assets/idtf_img') if _have_content('assets/idtf_img') == False else None
    
    _extract_rar('assets/mc_img.rar','assets/mc_img') if _have_content('assets/mc_img') == False else None
    _extract_rar('assets/tf_img.rar','assets/tf_img') if _have_content('assets/tf_img') == False else None

"""
def _delete_all_contents(directory):
    # Get a list of all files and directories in the specified directory
    contents = os.listdir(directory)
    
    # Iterate over each item in the directory
    for item in contents:
        # Construct the full path of the item
        item_path = os.path.join(directory, item)
        
        # Check if the item is a file
        if os.path.isfile(item_path):
            # Delete the file
            os.remove(item_path)
        # If the item is a directory
        elif os.path.isdir(item_path):
            # Delete the directory and its contents recursively
            os.rmdir(item_path)

def remove_all_images():
    _delete_all_contents('assets/idtf_img')
    _delete_all_contents('assets/mc_img')
    _delete_all_contents('assets/tf_img')



def _stitch_images_horizontally(filepaths):
    # List to store loaded images
    images = []
    print(filepaths)
    # Load each image from filepaths
    for filepath in filepaths[::-1]:
        
        if filepath is not None:
            image = cv2.imread(filepath)
            images.append(image)
            print(image.shape)
        else:
            continue
            print(f"Failed to load image: {filepath}")

    # Find the largest width and height among the images
    max_width = max(image.shape[1] for image in images)*3
    max_height = max(image.shape[0] for image in images)

    # Create a blank canvas with dimensions equal to the largest width and height
    canvas = np.ones((max_height, max_width * len(images), 3), dtype=np.uint8) * 255

    # Paste each image onto its original position on the canvas
    x_offset = canvas.shape[1]
    for image in images:
        x_offset -= image.shape[1]
        canvas[:image.shape[0], x_offset:x_offset + image.shape[1]] = image

    
    return canvas

def _crop_by_ratio(image, ratio=None):
    # Example 3-channel image array (695x1246x3)
    print(image.shape)
    image_array = image  # Create an example image array filled with zeros

    # Adding three rows of zeros to each channel
    new_rows = np.ones((40, image_array.shape[1], image_array.shape[2]), dtype=image_array.dtype)*255
    extended_image_array = np.vstack((image_array, new_rows))
    image = extended_image_array
    print(image.shape)
    if ratio is None:
        ratio = 13 / 8.5  # Default ratio for long size bond paper

    # Calculate the width to crop based on the ratio
    crop_width = int(image.shape[0] * ratio)

    # Calculate the remaining width after cropping
    remaining_width = image.shape[1] - crop_width

    # Crop the image, leaving the left side
    cropped_image = image[:, remaining_width:]
    print('correct_ratio',ratio)
    # Print information for debugging
    print("Original image shape:", image.shape)
    print("Cropped image shape:", cropped_image.shape)
    print("Expected ratio:", cropped_image.shape[1] / cropped_image.shape[0])
    
    #if cropped_image.shape[0] < cropped_image.shape[1]:
     #   print("IS SHORTER")
      #  return _crop_by_ratio(image, ratio=8.5/13)
    #else:
     #   print("IS LONGER")
    return cropped_image




def _stitch_header(image, header_filepath,title,padding=20, empty=False):
    # Load header image
    header_image = cv2.imread(header_filepath)
    if header_image is None:
        print(f"Failed to load header image: {header_filepath}")
        return None
    if empty:
        header_image = np.ones_like(header_image)*255
    images = [header_image, image]

    # Find the largest width among the images
    max_width = max(image.shape[1] for image in images)
    
    # Calculate the total height of the stitched image
    total_height = sum(image.shape[0] for image in images)

    # Create a blank canvas with dimensions equal to the largest width and total height
    canvas = np.ones((total_height, max_width, 3), dtype=np.uint8) * 255

    # Paste each image onto its original position on the canvas
    y_offset = 0
    for img in images:
        # Calculate the x-coordinate for the image to be aligned to the rightmost side
        x_offset = max_width - img.shape[1]
        canvas[y_offset:y_offset + img.shape[0], x_offset:x_offset + img.shape[1]] = img
        y_offset += img.shape[0]

    # Add padding around the stitched image
    padded_canvas = np.ones((canvas.shape[0] + 2 * padding, canvas.shape[1] + 2 * padding, 3), dtype=np.uint8) * 255
    padded_canvas[padding:-padding, padding:-padding] = canvas

    return padded_canvas

def _add_title(image,title,scale=1):
    # Define text, position, font, and scale
    text = title
    position = (10,30+20)  # Coordinates of the top-left corner
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = scale
    font_color = (0,0,0)  # White color in BGR format
    thickness = 2  # Thickness of the text

    # Add text to the image
    cv2.putText(image, text, position, font, font_scale, font_color, thickness)
    return image


def fit_score(mc_num, tf_num, idtf_num):
    tf_col_weight = 1/11
    mc_col_weight = 1/7
    idtf_col_weight = 0.5
    # checks if layout is going to be okay given number of items per category
    a = mc_col_weight*math.ceil(mc_num/25)
    b = tf_col_weight*math.ceil(tf_num/25)
    c = idtf_col_weight*math.ceil(idtf_num/10)
    total = a+b+c
    total_np = np.array([a,b,c])
    print(total_np)
    total_np = (total_np>0).sum()
    print(total_np)
    if total_np > 1:
        total_np -= 1
        total = total + (0.05*total_np)
        print(total_np)
    return total
        

def stich_all_image(mc_num, tf_num, idtf_num,title, save_path=None, filepaths=None, stitch_header=True, empty_header = False, font_scale=None):
    """stitch all images.
    returns filepath of template
    """
    print('stitching all images starting')
    if save_path is None:
        print('save path is None')
        save_path = 'assets/whole_template.png'
    
    header_path = 'assets/header.png'
    if filepaths is None:
        print('file path is non')
        filepaths = [f'assets/mc_img/{int(mc_num)}.png' if mc_num > 0 else None, 
                 f'assets/tf_img/{int(tf_num)}.png' if tf_num>0 else None, 
                 f'assets/idtf_img/{int(idtf_num)}.png' if idtf_num>0 else None]
    print(filepaths)
    if mc_num == 0 and tf_num == 0 and idtf_num == 0:
        return 'assets/empty_template.png'
    else:
        print('stitching image orizontally')
        type_test_image = _stitch_images_horizontally(filepaths)
        print('stitching header')
        stitched_image = _stitch_header(type_test_image, header_path, title,empty=True if empty_header else False ) if stitch_header==True else type_test_image
        print('cropping by ratio')
        stitched_image = _crop_by_ratio(stitched_image)
        print('adding title')
        stitched_image = _add_title(stitched_image, title,scale=0.75 if font_scale is None else font_scale) 
        print('saving')
        cv2.imwrite(save_path, stitched_image)
        save_path2 = save_path[:-4] + '-flipped.png'
        cv2.imwrite(save_path2, cv2.rotate(stitched_image, cv2.ROTATE_90_CLOCKWISE))
        print('saving done')
        return save_path