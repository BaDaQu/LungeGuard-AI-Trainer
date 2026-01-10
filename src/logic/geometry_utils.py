import math


class GeometryUtils:
    @staticmethod
    def calculate_angle(a, b, c):
        """
        Oblicza kąt (w stopniach) między trzema punktami a, b, c.
        Punkt b jest wierzchołkiem kąta.
        """
        # Rozpakowanie współrzędnych [id, x, y, z] -> bierzemy x, y
        x1, y1 = a[1], a[2]
        x2, y2 = b[1], b[2]
        x3, y3 = c[1], c[2]

        # Obliczenie kąta w radianach
        radians = math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2)
        angle = abs(radians * 180.0 / math.pi)
        # ----------------------------------------------------

        # Normalizacja kąta do przedziału 0-180
        if angle > 180.0:
            angle = 360 - angle

        return round(angle, 1)