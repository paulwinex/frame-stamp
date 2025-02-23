from __future__ import absolute_import

import math
from .point import Point


def rotate_point_around_point(point, center, angle):
    theta = math.radians(angle)
    x, y = point
    cx, cy = center
    x_new = cx + (x - cx) * math.cos(theta) - (y - cy) * math.sin(theta)
    y_new = cy + (x - cx) * math.sin(theta) + (y - cy) * math.cos(theta)
    return x_new, y_new


def rotate_point(point: list, angle, origin: list = None,  precision=3):
    """
    Rotate a point counterclockwise by a given angle around a given origin.
    The angle should be given in degrees.

    """
    origin = origin or (0, 0)
    ox, oy = origin
    px, py = point
    rad = math.radians(angle)
    qx = ox + math.cos(rad) * (px - ox) - math.sin(rad) * (py - oy)
    qy = oy + math.sin(rad) * (px - ox) + math.cos(rad) * (py - oy)
    return round(qx, precision), round(qy, precision)


def get_rectangle_points(rect, angle=0):
    """Returns the coordinates of the corners of a rectangle, taking into account rotation."""
    if all(isinstance(val, (int, float)) for val in rect):
        x0, y0, x1, y1 = rect
        points = [
            (x0, y0),
            (x1, y0),
            (x1, y1),
            (x0, y1)
        ]
        if angle != 0:
            center_x = (x0 + x1) / 2
            center_y = (y0 + y1) / 2
            points = [rotate_point(point, angle, (center_x, center_y)) for point in points]
    elif all(isinstance(val, tuple) for val in rect):
        if angle != 0:
            aver_point: Point = sum([Point(*x) for x in rect], Point(0, 0)) / (len(rect) - 1)
            points = [rotate_point(point, angle, (aver_point.x, aver_point.y)) for point in rect]
        else:
            points = rect
    else:
        raise ValueError(f"Invalid rectangle format: {rect}")
    return points


def separating_axis_theorem(rect1, rect2):
    """Tests the intersection of two convex polygons using the separating axis theorem."""
    def get_normals(points):
        """Returns the normals to the sides of a polygon."""
        normal_list = []
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            edge = (p2[0] - p1[0], p2[1] - p1[1])
            normal = (-edge[1], edge[0])
            normal_list.append(normal)
        return normal_list

    def project(points, axis):
        """Projects points onto an axis and returns the minimum and maximum values of the projection."""
        min_proj = max_proj = None
        for point in points:
            proj = point[0] * axis[0] + point[1] * axis[1]
            if min_proj is None or proj < min_proj:
                min_proj = proj
            if max_proj is None or proj > max_proj:
                max_proj = proj
        return min_proj, max_proj

    points1 = get_rectangle_points(rect1)
    points2 = get_rectangle_points(rect2)

    for points in [points1, points2]:
        normals = get_normals(points)
        for normal in normals:
            min1, max1 = project(points1, normal)
            min2, max2 = project(points2, normal)
            if max1 < min2 or max2 < min1:
                return False
    return True


def check_intersection(rect1, rect2, angle1=0, angle2=0, index=0):
    """Checks the intersection of two rectangles, taking into account rotation."""
    if angle1 != 0 or angle2 != 0:
        points1 = get_rectangle_points(rect1, angle1)
        points2 = get_rectangle_points(rect2, angle2)
        if index == 231:
            print('PTS1', points1)
            print('PTS2', points2)
        return separating_axis_theorem(points1, points2)
    else:
        x0_1, y0_1, x1_1, y1_1 = rect1
        x0_2, y0_2, x1_2, y1_2 = rect2
        return not (x1_1 < x0_2 or x1_2 < x0_1 or y1_1 < y0_2 or y1_2 < y0_1)


def distance(point1, point2):
    """Calculates the Euclidean distance between two points."""
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


def get_row_distances(matrix, deleting_pivot):
    """Returns a list of distances from each row to the deleting pivot point."""
    row_distances = []
    for row in matrix:
        row_center = [sum(col[0] for col in row) / len(row), sum(col[1] for col in row) / len(row)]
        row_distances.append(distance(row_center, deleting_pivot))
    return row_distances


def get_column_distances(matrix, deleting_pivot):
    """Returns a list of distances from each column to the deleting_pivot point."""
    column_distances = []
    for col_idx in range(len(matrix[0])):
        col_center = [sum(row[col_idx][0] for row in matrix) / len(matrix), sum(row[col_idx][1] for row in matrix) / len(matrix)]
        column_distances.append(distance(col_center, deleting_pivot))
    return column_distances


def remove_excess_elements(matrix, max_rows, max_columns, deleting_pivot):
    """Removes extra rows and columns from the matrix."""
    if max_rows == 0 or max_columns == 0:
        return []

    row_distances = get_row_distances(matrix, deleting_pivot)
    column_distances = get_column_distances(matrix, deleting_pivot)

    # Sort row and column indices by distance
    sorted_row_indices = sorted(range(len(row_distances)), key=lambda i: row_distances[i])
    sorted_column_indices = sorted(range(len(column_distances)), key=lambda i: column_distances[i])

    # We leave only max_rows and max_columns
    selected_row_indices = sorted_row_indices[:max_rows] if max_rows is not None else sorted_row_indices
    selected_column_indices = sorted_column_indices[:max_columns] if max_columns is not None else sorted_column_indices

    # Create a new matrix with the selected rows and columns
    new_matrix = []
    for row_idx in selected_row_indices:
        new_row = [matrix[row_idx][col_idx] for col_idx in selected_column_indices]
        new_matrix.append(new_row)

    return new_matrix


def rectangles_intersect(rect1, rect2):
    """
    Checks whether two rectangles intersect using the separating axis method (SAT).
    """
    def get_edges(rect):
        return [(rect[i][0] - rect[i - 1][0], rect[i][1] - rect[i - 1][1]) for i in range(len(rect))]

    def get_normals(edges):
        return [(-edge[1], edge[0]) for edge in edges]

    def project(rect, axis):
        dots = [(point[0] * axis[0] + point[1] * axis[1]) for point in rect]
        return min(dots), max(dots)

    def overlap(proj1, proj2):
        return proj1[1] >= proj2[0] and proj2[1] >= proj1[0]
    edges1 = get_edges(rect1)
    edges2 = get_edges(rect2)
    normals = get_normals(edges1) + get_normals(edges2)
    for normal in normals:
        proj1 = project(rect1, normal)
        proj2 = project(rect2, normal)
        if not overlap(proj1, proj2):
            return False
    return True


def rect_in_canvas(rect_points, canvas_width, canvas_height):
    for x, y in rect_points:
        if 0 <= x <= canvas_width and 0 <= y <= canvas_height:
            return True

    canvas_points = [(0, 0), (canvas_width, 0), (canvas_width, canvas_height), (0, canvas_height)]
    all_canvas_inside = all(is_point_inside_polygon(cx, cy, rect_points) for cx, cy in canvas_points)
    if all_canvas_inside:
        return True
    return False


def is_point_inside_polygon(x, y, poly):
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(1, n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if x <= xinters:
                            inside = not inside
                    else:
                        if p1x <= x <= p2x or p2x <= x <= p1x:
                            return True
        p1x, p1y = p2x, p2y
    return inside
