import math
import warnings
from . import Indicator
from ..sources import Source
from ..timelapses import Timelapse
from ..utils.mappers.side_pluckers import SidePlucker


class PredictorAlgorithm:
    """
    A predictor algorithm takes an array of elements
    and makes a prediction. It also provides metadata
    of itself that involves interaction with the data
    provided to the indicator.
    """

    def _get_tail_size(self):
        raise NotImplemented

    @property
    def tail_size(self):
        """
        The tail size is: how many elements does this
        predictor instance requires in order to make
        a predictor. If less than those elements are
        provided, then NaN will be the value of both
        the prediction and the structural error of that
        prediction in particular.
        :return: The tail size.
        """

        return self._get_tail_size()

    def _get_step(self):
        raise NotImplemented

    @property
    def step(self):
        """
        The step is: how many steps in the future will this
        predictor instance actually predict. These objects
        consider X to be expressed in units of time, which
        makes the corresponding Y value a function of time,
        which might be a linear or polynomial expression
        or whatever is needed to make a prediction. In this
        case, the step can be freely chosen.

        Unstructured time-series prediction will typically
        have step=1 (constant), while layered time-series
        prediction (where first is the trend, then the season,
        and finally the stationary data) may predict step=N
        while not considering the stationary part important
        enough to suffer when its "long-term" prediction
        converges to a constant.
        """

        return self._get_step()


class Predictor(Indicator):
    """
    This is a one-way predictor. Given a series of values, it predicts
    the next value and also provides a bunch of auxiliary values to
    take a look to (e.g. structural coefficient and some notion of MSE
    or related stuff).
    """

    def __init__(self, timelapse: Timelapse, algorithm: PredictorAlgorithm,
                 side: int = None):
        super().__init__(timelapse)

        # First, initialize which data will be read from.
        self._data = None
        if isinstance(timelapse, Source):
            if side not in [Source.BID, Source.ASK]:
                raise ValueError("When creating a Predictor indicator from a Source, "
                                 "a side must be chosen and must be either Source.BID "
                                 "or Source.ASK")
            self._data = SidePlucker(timelapse, side)
        elif isinstance(timelapse, Indicator):
            if timelapse.width != 1:
                raise ValueError("When creating a Predictor indicator from another indicator, "
                                 "the width of that indicator must be 1. So far, multi-dimensional "
                                 "indicators are not supported yet")
            self._data = timelapse
        else:
            raise TypeError("The timelapse must be either a Source or an Indicator")

        # Then, set the predictor instance.
        if not isinstance(algorithm, PredictorAlgorithm) or type(algorithm) == PredictorAlgorithm:
            raise TypeError("The algorithm must be specified and it must be of a strict "
                            "subclass of PredictorAlgorithm")
        self._algorithm = algorithm

    def _initial_width(self):
        """
        The initial width for the indicator involves columns:
        - The vector for the prediction.
        - The vector for the structural error for the moment where the prediction was done.
        - The vector for the structural error for the moment the prediction was done for.
        - The difference between the actual value and the prediction.
        - The standard deviation, taking a proper tail, considering prediction-actual.
        """

        return 5

    @property
    def tail_size(self):
        """
        The underlying tail size, according to the algorithm.
        """

        return self._algorithm.tail_size

    @property
    def step(self):
        """
        The distance between the time of the last sample and the
        time, in the future, being predicted.
        """

        return self._algorithm.step
