import math


def _is_numeric(obj):
    """Return True if the object is a numeric type.

    In Python 3 the builtin ``long`` type no longer exists, so we simply
    check against ``int`` and ``float``. This helper exists because the
    original implementation targeted Python 2 and performed a similar
    check. Keeping this function allows older call sites to work
    unchanged while ensuring compatibility with Python 3.
    """
    # In Python 3 ``long`` is just an alias of ``int``, so there is no
    # need to explicitly reference it. Future numeric types such as
    # ``decimal.Decimal`` are intentionally not handled here because the
    # vector math in this game expects plain floats or ints.
    return isinstance(obj, (int, float))


class Vector:
    """Simple 2‑D vector implementation with arithmetic helpers.

    This class was originally written for Python 2 and has been updated
    to support Python 3. All arithmetic operators return new
    :class:`Vector` instances leaving the originals unchanged.
    """

    def __init__(self, a=0, b=0):
        """Construct a new vector.

        You can either pass two numeric values ``a`` and ``b`` which
        become the ``x`` and ``y`` components respectively, or pass two
        iterable sequences of length two. In the latter case the
        resulting vector is the difference ``b - a``.
        """
        if _is_numeric(a):
            # Assume two numbers
            self.x = a
            self.y = b
        else:
            # Assume sequences and compute the difference
            self.x = b[0] - a[0]
            self.y = b[1] - a[1]

    def __getitem__(self, index):
        """Access components by index ``0`` (x) or ``1`` (y)."""
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        else:
            raise IndexError("Vector index out of range")

    def __add__(self, other):
        """Return the vector sum ``self + other``."""
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        """Return the vector difference ``self - other``."""
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        """Return a new vector scaled by ``other``.

        Only scalar multiplication is supported. Attempting to multiply
        by a non‑numeric type will raise a ``TypeError``.
        """
        if not _is_numeric(other):
            raise TypeError("Only scalar multiplication is supported.")
        return Vector(other * self.x, other * self.y)

    def __rmul__(self, other):
        """Implement right multiplication to allow ``scalar * vector``."""
        return self.__mul__(other)

    def __truediv__(self, other):
        """Return a new vector divided by ``other``.

        Division by non‑numeric values will propagate the underlying
        ``TypeError``.
        """
        if not _is_numeric(other):
            raise TypeError("Only scalar division is supported.")
        return Vector(self.x / other, self.y / other)

    # Provide Python 2 compatibility alias. This method will never be
    # invoked under Python 3 but keeps the API symmetric for
    # completeness.
    __div__ = __truediv__

    def __neg__(self):
        """Return the negation of the vector."""
        return Vector(-self.x, -self.y)

    def __abs__(self):
        """Return the magnitude of the vector using ``abs(vec)``."""
        return self.length()

    def __repr__(self):
        return f"({self.x}, {self.y})"

    def __str__(self):
        return f"({self.x}, {self.y})"

    def dot(self, vector):
        """Return the dot product between this vector and ``vector``."""
        return self.x * vector.x + self.y * vector.y

    def cross(self, vector):
        """Return the 2‑D cross product (scalar) between this vector and
        ``vector``."""
        return self.x * vector.y - self.y * vector.x

    def length(self):
        """Return the Euclidean length of the vector."""
        return math.sqrt(self.dot(self))

    def perpindicular(self):
        """Return a vector perpendicular to this one."""
        return Vector(-self.y, self.x)

    def unit(self):
        """Return a unit vector in the direction of this vector."""
        l = self.length()
        if l == 0:
            return Vector(0, 0)
        return self / l

    def projection(self, vector):
        """Return the projection of this vector onto ``vector``."""
        k = (self.dot(vector)) / vector.length()
        return k * vector.unit()

    def angle(self, vector=None):
        """Return the angle between this vector and ``vector`` in
        radians.

        If no ``vector`` is given, the angle is measured relative to the
        positive x‑axis.
        """
        if vector is None:
            vector = Vector(1, 0)
        return math.acos((self.dot(vector)) / (self.length() * vector.length()))

    def angle_in_degrees(self, vector=None):
        """Return the angle between this vector and ``vector`` in
        degrees."""
        return (self.angle(vector) * 180) / math.pi
