from __future__ import division
from math import sqrt

class Point(object):
    __slots__ = ['x', 'y']
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @staticmethod
    def distance (a, b):
        return sqrt( (b.y - a.y)**2 + (b.x - a.x)**2 )

    @classmethod
    def weighted_average(cls, a, dist, b):

        x = (1 - dist) * a.x + dist * b.x
        y = (1 - dist) * a.y + dist * b.y

        if isinstance(a, Point3D) and isinstance(b, Point3D):
            symp = a.symp.weighted_average(a.symp, dist, b.symp)
        else:
            symp = a.symp if isinstance(a, Point3D) else \
                   b.symp if isinstance(b, Point3D) else None

        if symp:
            return Point3D(x, y, symp=symp)
        else:
            return Point2D(x, y)

    def new_alike(self, x, y):
        return self.__class__(x, y)

    def __getitem__(self, n):
        if n > 1: return IndexError
        return self.y if n else self.x

    def __len__(self): return 2

class Point2D(Point): pass

class Point3D(Point):
      __slots__ = ['env']
      def __init__(self, *args, **kwargs):
          symp = kwargs.pop('symp')
          if not symp:
              raise AttributeError("Missing an envelope for Point3D instance")
          super(Point, self).__init__(*args, **kwargs)
          self.symp = symp

      def new_alike(self, x, y, symp):
          return self.__class__(x, y, symp=symp)

      def __getitem__(self, n):
          return self.symp if n == 2 else Point.__getitem__(self, n)

      def __len__(self): return 3