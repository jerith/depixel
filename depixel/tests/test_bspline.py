from unittest import TestCase

from depixel.bspline import Point, BSpline


def make_oct_spline(p=2, offset_x=0, offset_y=0, scale=50):
    base = [(2, 2), (4, 2), (5, 3), (5, 5), (4, 6), (2, 6), (1, 5), (1, 3)]
    points = [(x * scale + offset_x, y * scale + offset_y) for x, y in base]
    points = points + points[:p]
    m = len(points) + p
    knots = [float(i) / m for i in range(m + 1)]
    return BSpline(knots, points, p)


class TestBSpline(TestCase):
    def test_spline_degree(self):
        knots = [0, 0.25, 0.5, 0.75, 1]
        points = [(0, 0), (1, 1)]
        self.assertEqual(2, BSpline(knots, points).degree)
        self.assertEqual(2, BSpline(knots, points, 2).degree)
        try:
            BSpline(knots, points, 3)
            self.fail("Expected ValueError.")
        except ValueError, e:
            self.assertEqual("Expected degree 2, got 3.", e.args[0])

    def test_spline_domain(self):
        spline = make_oct_spline()
        self.assertEqual((0.5 / 3, 1 - 0.5 / 3), spline.domain)
        self.assertEqual((spline.knots[2], spline.knots[-3]), spline.domain)

    def test_spline_point_at_knot(self):
        spline = make_oct_spline()
        self.assertEqual(Point((150, 300)), spline(0.5).round())

    def test_spline_derivative(self):
        spline = make_oct_spline()
        deriv = spline.derivative()
        self.assertEqual(deriv.degree, spline.degree - 1)
        self.assertEqual(deriv.knots, spline.knots[1:-1])
        self.assertEqual(len(deriv.points), len(spline.points) - 1)

    def test_curvature(self):
        spline = make_oct_spline()
        self.assertEqual(0.005, round(spline.curvature(0.5), 5))
