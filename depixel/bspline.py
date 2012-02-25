# -*- test-case-name: depixel.tests.test_bspline -*-

"""
This is a limited quadratic B-spline library.

The mathematics mostly comes from some excellent course notes on the web:

http://www.cs.mtu.edu/~shene/COURSES/cs3621/NOTES/

More specifically, De Boor's Algorithm is at:

http://www.cs.mtu.edu/~shene/COURSES/cs3621/NOTES/spline/B-spline/de-Boor.html

Errors are likely due to my lack of understanding rather than any deficiency in
the source material. I don't completely understand the underlying theory, so I
may have done something silly. However, my tests seem to do the right thing.
"""

import random
from math import sqrt


class BSpline(object):
    """
    This is made out of mathematics. You have been warned.

    A B-spline has:
      * n + 1 control points
      * m + 1 knots
      * degree p
      * m = n + p + 1
    """
    def __init__(self, knots, points, degree=None):
        self.knots = tuple(knots)
        self._points = list(points)
        expected_degree = len(self.knots) - len(self._points) - 1
        if degree is None:
            degree = expected_degree
        if degree != expected_degree:
            raise ValueError("Expected degree %s, got %s." % (
                expected_degree, degree))
        self.degree = degree
        self._reset_cache()

    def _reset_cache(self):
        self._cache = {}

    def move_point(self, i, value):
        self._points[i] = value
        self._reset_cache()

    def __str__(self):
        return "<%s degree=%s, points=%s, knots=%s>" % (
            type(self).__name__,
            self.degree, len(self.points), len(self.knots))

    def copy(self):
        return type(self)(self.knots, self.points, self.degree)

    @property
    def domain(self):
        return (self.knots[self.degree],
                self.knots[len(self.knots) - self.degree - 1])

    @property
    def points(self):
        return tuple(self._points)

    @property
    def useful_points(self):
        return self.points

    def __call__(self, u):
        """
        De Boor's Algorithm. Made out of more maths.
        """
        s = len([uk for uk in self.knots if uk == u])
        for k, uk in enumerate(self.knots):
            if uk >= u:
                break
        if s == 0:
            k -= 1
        if self.degree == 0:
            if k == len(self.points):
                k -= 1
            return self.points[k]
        ps = [dict(zip(range(k - self.degree, k - s + 1),
                       self.points[k - self.degree:k - s + 1]))]

        for r in range(1, self.degree - s + 1):
            ps.append({})
            for i in range(k - self.degree + r, k - s + 1):
                a = (u - self.knots[i]) / (self.knots[i + self.degree - r + 1]
                                           - self.knots[i])
                ps[r][i] = (
                    (1 - a) * ps[r - 1][i - 1][0] + a * ps[r - 1][i][0],
                    (1 - a) * ps[r - 1][i - 1][1] + a * ps[r - 1][i][1])
        return ps[-1][k - s]

    def quadratic_bezier_segments(self):
        """
        Extract a sequence of quadratic Bezier curves making up this spline.

        NOTE: This assumes our spline is quadratic.
        """
        assert self.degree == 2
        control_points = self.points[1:-1]
        on_curve_points = [self(u) for u in self.knots[2:-2]]
        ocp0 = on_curve_points[0]
        for cp, ocp1 in zip(control_points, on_curve_points[1:]):
            yield (ocp0, cp, ocp1)
            ocp0 = ocp1

    def derivative(self):
        """
        Take the derivative.
        """
        cached = self._cache.get('derivative')
        if cached:
            return cached

        new_points = []
        p = self.degree
        for i in range(0, len(self.points) - 1):
            coeff = p / (self.knots[i + 1 + p] - self.knots[i + 1])
            new_points.append((
                    coeff * (self.points[i + 1][0] - self.points[i][0]),
                    coeff * (self.points[i + 1][1] - self.points[i][1])))

        cached = BSpline(self.knots[1:-1], new_points, p - 1)
        self._cache['derivative'] = cached
        return cached

    def _clamp_domain(self, value):
        return max(self.domain[0], min(self.domain[1], value))

    def _get_span(self, index):
        return (self._clamp_domain(self.knots[index]),
                self._clamp_domain(self.knots[index + 1]))

    def _get_point_spans(self, index):
        return [self._get_span(index + i) for i in range(self.degree)]

    def integrate_over_span(self, func, span, intervals):
        if span[0] == span[1]:
            return 0

        interval = (span[1] - span[0]) / intervals
        result = (func(span[0]) + func(span[1])) / 2
        for i in xrange(1, intervals):
            result += func(span[0] + i * interval)
        result *= interval

        return result

    def integrate_for(self, index, func, intervals):
        spans_ = self._get_point_spans(index)
        spans = [span for span in spans_ if span[0] != span[1]]
        return sum(self.integrate_over_span(func, span, intervals)
                   for span in spans)

    def curvature(self, u):
        drv1 = self.derivative()
        drv2 = drv1.derivative()
        d1, d2 = drv1(u), drv2(u)
        num = abs(d1[0] * d2[1] - d2[0] * d1[1])
        den = sqrt((d1[0] ** 2 + d1[1] ** 2) ** 3)
        if den == 0:
            return 0
        return num / den

    def curvature_energy(self, index, intervals_per_span):
        return self.integrate_for(index, self.curvature, intervals_per_span)

    def reversed(self):
        return type(self)(
            (1 - k for k in reversed(self.knots)), reversed(self._points),
            self.degree)


class ClosedBSpline(BSpline):
    def __init__(self, knots, points, degree=None):
        super(ClosedBSpline, self).__init__(knots, points, degree)
        self._unwrapped_len = len(self._points) - self.degree
        self._check_wrapped()

    def _check_wrapped(self):
        if self._points[:self.degree] != self._points[-self.degree:]:
            raise ValueError(
                "Points not wrapped at degree %s." % (self.degree,))

    def move_point(self, index, value):
        if not 0 <= index < len(self._points):
            raise IndexError(index)
        index = index % self._unwrapped_len
        super(ClosedBSpline, self).move_point(index, value)
        if index < self.degree:
            super(ClosedBSpline, self).move_point(
                index + self._unwrapped_len, value)

    @property
    def useful_points(self):
        return self.points[:-self.degree]

    def _get_span(self, index):
        span = lambda i: (self.knots[i], self.knots[i + 1])
        d0, d1 = span(index)
        if d0 < self.domain[0]:
            d0, d1 = span(index + len(self.points) - self.degree)
        elif d1 > self.domain[1]:
            d0, d1 = span(index + self.degree - len(self.points))
        return self._clamp_domain(d0), self._clamp_domain(d1)


def polyline_to_closed_bspline(path, degree=2):
    """
    Make a closed B-spline from a path through some nodes.
    """

    points = path + path[:degree]
    m = len(points) + degree
    knots = [float(i) / m for i in xrange(m + 1)]

    return ClosedBSpline(knots, points, degree)


class SplineSmoother(object):
    INTERVALS_PER_SPAN = 10
    POINT_GUESSES = 10
    GUESS_OFFSET = 0.02
    ITERATIONS = 10

    # INTERVALS_PER_SPAN = 5
    # POINT_GUESSES = 1
    # ITERATIONS = 1

    def __init__(self, spline):
        self.orig = spline
        self.spline = spline.copy()

    def _e_curvature(self, index):
        return self.spline.curvature_energy(index, self.INTERVALS_PER_SPAN)

    def _e_positional(self, index):
        orig = self.orig.points[index]
        point = self.spline.points[index]
        e_positional = sum((p[0] - p[1]) ** 2 for p in zip(point, orig)) ** 2
        return e_positional

    def point_energy(self, index):
        e_curvature = self._e_curvature(index)
        e_positional = self._e_positional(index)
        return e_positional + e_curvature

    def _rand(self):
        return (random.random() - 0.5) * self.GUESS_OFFSET

    def smooth_point(self, index, start):
        energies = [(self.point_energy(index), start)]
        for _ in range(self.POINT_GUESSES):
            point = tuple(i + self._rand() for i in start)
            self.spline.move_point(index, point)
            energies.append((self.point_energy(index), point))
        self.spline.move_point(index, min(energies)[1])

    def smooth(self):
        print "."
        for _it in range(self.ITERATIONS):
            # print "IT:", _it
            for i, point in enumerate(self.spline.useful_points):
                self.smooth_point(i, point)


def smooth_spline(spline):
    smoother = SplineSmoother(spline)
    smoother.smooth()
    return smoother.spline
