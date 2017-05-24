from __future__ import print_function
from __future__ import division

import cv2
import argparse
import os

cascade_path = os.path.dirname(__file__) + '/cascades/haarcascade_frontalface_default.xml'

def center_from_faces(matrix):
    face_cascade = cv2.CascadeClassifier(cascade_path)
    faces = face_cascade.detectMultiScale(matrix, 1.3, 5)

    x = 0
    y = 0
    weight = 0

    for (x, y, w, h) in faces:
        print('Face detected at ', x, y, w, h)
        weight += w * h
        x += (x + w / 2) * w * h
        y += (y + h / 2) * w * h

    if len(faces) == 0:
        return False

    return {
        'x': x / weight,
        'y': y / weight
    }


def center_from_good_features(matrix):
    x = 0
    y = 0
    weight = 0

    max_corners = 50
    quality_level = 0.1
    min_distance = 10

    corners = cv2.goodFeaturesToTrack(matrix, max_corners, quality_level, min_distance)

    for point in corners:
        weight += 1
        x += point[0][0]
        y += point[0][1]

    return {
        'x': x / weight,
        'y': y / weight
    }


def crop_vertical_pos(center, original_width, original_height, target_width, target_height):
    new_height = target_height / target_width * original_width
    top = max(round(center['y'] - new_height / 2), 0)
    bottom = min(top + new_height, original_height)

    return {
        'left': 0,
        'right': original_width,
        'top': top,
        'bottom': bottom
    }


def crop_horizontal_pos(center, original_width, original_height, target_width, target_height):
    new_width = target_width / target_height * original_height
    left = max(round(center['x'] - new_width / 2), 0)
    right = min(left + new_width, original_width)

    return {
        'left': left,
        'right': right,
        'top': 0,
        'bottom': original_height
    }


def smart_crop(image, target_width, target_height, destination, do_resize):
    # read grayscale image
    original = cv2.imread(image)

    if original is None:
        print("Could not read source image")
        exit(1)

    height, width, depth = original.shape

    target_height = int(target_height)
    target_width = int(target_width)

    matrix = cv2.imread(image, cv2.CV_LOAD_IMAGE_GRAYSCALE)

    if do_resize:
        ratio = max(target_width / width, target_height / height)

        width, height = original.shape[1] * ratio, original.shape[0] * ratio
        original = cv2.resize(original, (int(width), int(height)))
        matrix = cv2.resize(matrix, (int(width), int(height)))

    center = center_from_faces(matrix)

    if not center:
        print('Using Good Feature Tracking method')
        center = center_from_good_features(matrix)

    print('Found center: ', center)

    if width / height < target_width / target_height:
        crop_pos = crop_vertical_pos(center, width, height, target_width, target_height)
    else:
        crop_pos = crop_horizontal_pos(center, width, height, target_width, target_height)

    print('Crop: ', crop_pos)

    cropped = original[crop_pos['top']: crop_pos['bottom'], crop_pos['left']: crop_pos['right']]
    cv2.imwrite(destination, cropped)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-W", "--width", required=True, help="Target width")
    ap.add_argument("-H", "--height", required=True, help="Target height")
    ap.add_argument("-i", "--image", required=True, help="Image to crop")
    ap.add_argument("-o", "--output", required=True, help="Output")
    ap.add_argument("-n", "--no-resize", required=False, default=False, action="store_true", help="Don't resize image before treating it")

    args = vars(ap.parse_args())

    smart_crop(args["image"], args["width"], args["height"], args["output"], not args["no_resize"])


if __name__ == '__main__':
    main()