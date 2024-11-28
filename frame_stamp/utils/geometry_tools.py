import math


def rotate_point_around_point(point, center, angle):
    theta = math.radians(angle)
    x, y = point
    cx, cy = center
    x_new = cx + (x - cx) * math.cos(theta) - (y - cy) * math.sin(theta)
    y_new = cy + (x - cx) * math.sin(theta) + (y - cy) * math.cos(theta)
    return x_new, y_new
