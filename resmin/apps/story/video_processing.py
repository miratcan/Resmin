import os
import time
import math
import hashlib
import subprocess

from PIL import Image

from django.conf import settings


def grab_frame(video_path, frames=100):

    histogram_list = []
    frame_average = []

    path, full_filename = os.path.split(video_path)
    filename, extension = os.path.splitext(full_filename)

    # By default temp frame data is stored under MEDIA_ROOT/temp
    # Make sure this directory exists.
    path = "%s/temp/" % settings.MEDIA_ROOT
    if not os.path.isdir(path):
        os.mkdir(path)

    hashable_value = "%s%s" % (full_filename, int(time.time()))
    filehash = hashlib.md5(hashable_value).hexdigest()

    frame_args = {'path': path, 'filename': filehash, 'frame': '%d'}
    frame = "%(path)s%(filename)s.%(frame)s.jpg" % frame_args

    # Build the ffmpeg shell command and run it via subprocess
    cmd_args = {'frames': frames, 'video_path': video_path,
                'output': frame, 'ffmpeg_path': settings.FFMPEG_PATH}
    command = "%(ffmpeg_path)s -i %(video_path)s -y -vframes " \
              "%(frames)d %(output)s"
    command = command % cmd_args
    response = subprocess.call(command, shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

    # Fail silently if ffmpeg is not installed.
    # the ffmpeg commandline tool that is.
    if response != 0:
        return None

    # Loop through the generated images, open, and
    # generate the image histogram.
    for index in range(1, frames + 1):
        frame_name = frame % index

        # If for some reason the frame does not exist, go to next frame.
        if not os.path.exists(frame_name):
            continue

        image = Image.open(frame_name)

        # Convert to RGB if necessary
        if image.mode not in ('L', 'RGB'):
            image = image.convert('RGB')

        histogram_list.append(image.histogram())

    frames = len(histogram_list)

    # Calculate the accumulated average.
    for idx in range(len(histogram_list[0])):
        average = 0.0
        accumulation = 0.0
        for idy in range(frames):
            accumulation += histogram_list[idy][idx]
            average = (float(accumulation) / frames)
        frame_average.append(average)

    minn = -1
    minRMSE = -1

    # Calculate the mean squared error
    for idx in range(frames):
        results = 0.0
        average_count = len(frame_average)

        for idy, average in enumerate(frame_average):
            error = average - float(histogram_list[idx][idy])
            results += float((error * error)) / average_count
        rmse = math.sqrt(results)

        if minn == -1 or rmse < minRMSE:
            minn = (idx + 1)
            minRMSE = rmse

    frame_path = frame % (minn)

    # Unlink temp files.
    frames = range(frames)
    del frames[minn - 1]
    for idx in frames:
        frame_file = frame % (idx + 1)
        os.unlink(frame_file)

    return frame_path
