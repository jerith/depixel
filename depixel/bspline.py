# -*- test-case-name: depixel.tests.test_bspline -*-

"""
This is a limited quadratic B-spline library.

The mathematics mostly comes from some excellent course notes on the web:

http://www.cs.mtu.edu/~shene/COURSES/cs3621/NOTES/

More specifically, De Boor's Algorithm is at:

http://www.cs.mtu.edu/~shene/COURSES/cs3621/NOTES/spline/B-spline/de-Boor.html

Errors are likely due to my lack of understanding rather than any deficiency in
the source material. I haven't put in the time and effort to completely
understand the underlying theory, so I may have done something silly. However,
my tests seem to do the right thing.
"""


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
        self.knots = knots
        self.points = points
        expected_degree = len(knots) - len(points) - 1
        if degree is None:
            degree = expected_degree
        if degree != expected_degree:
            raise ValueError("Expected degree %s, got %s." % (
                expected_degree, degree))
        self.degree = degree

    @property
    def domain(self):
        return (self.knots[self.degree], self.knots[-1 - self.degree])

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


def polyline_to_closed_bspline(path, degree=2):
    """
    Make a closed B-spline from a path through some nodes.
    """

    points = path + path[:degree]
    m = len(points) + degree
    knots = [float(i) / m for i in xrange(m + 1)]

    return BSpline(knots, points, degree)
