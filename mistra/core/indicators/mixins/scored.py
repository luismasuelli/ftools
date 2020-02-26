from numpy import float_, NaN
from ...growing_arrays import GrowingArray


class ScoredMixin:
    """
    Adds capability to track its own score (a measure of performance)
      while running its lifecycle. In the end, the scoring is a float
      value in the range starting at 0 (shit) and ending at 1 (perfect),
      or NaN if a score is not available.

    Indicators implementing this trait/mixin will have its own growing
      array holding the scores for each time. Ideally, scoring involves
      several factors that evolve in time, but ultimately each score
      value does not depend on former values (unless a metric implies
      such behaviour).

    Implementors will have access to the `_scores` protected member to
      put a score for a given time, and a public `get_score` member to
      get the score for certain time. When putting a score, all the
      times before the score time will have a NaN value.
    """

    def __init__(self):
        self._scores = GrowingArray(float_, NaN, 3600, 1)

    def get_score(self, time):
        return self._scores[time, 0]

