import datetime
import math
import warnings
from enum import IntEnum
from typing import Tuple
import numpy
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

    def predict(self, x: numpy.ndarray) -> Tuple[float, float]:
        """
        Makes a prediction. The result of the prediction is
        a tuple making: (prediction, structural_error).
        :param x: The input.
        :return: The prediction and the structural error.
        """

        raise NotImplemented

    def online_train(self, x: numpy.ndarray, y: float):
        """
        Trains the current algorithm given the new sample.
        :param x: The features vector.
        :param y: The corresponding endogenous value.
        """

        # The default algorithm is: to do nothing.


class Predictor(Indicator):
    """
    This is a one-way predictor. Given a series of values, it predicts
    the next value and also provides a bunch of auxiliary values to
    take a look to (e.g. structural coefficient and some notion of MSE
    or related stuff).
    """

    class Columns(IntEnum):
        PREDICTION = 0
        STRUCTURAL_ERROR = 1
        PREDICTION_DIFFERENCE = 2
        STANDARD_ERROR = 3

    def __init__(self, timelapse: Timelapse, algorithm: PredictorAlgorithm,
                 side: int = None, moving_stderr_tail_size: int = 20,
                 chunk_size: int = 3600):
        # First, initialize which data will be read from.
        self._input_data = None
        if isinstance(timelapse, Source):
            if side not in [Source.BID, Source.ASK]:
                raise ValueError("When creating a Predictor indicator from a Source, "
                                 "a side must be chosen and must be either Source.BID "
                                 "or Source.ASK")
            self._input_data = SidePlucker(timelapse, side)
        elif isinstance(timelapse, Indicator):
            if timelapse.width != 1:
                raise ValueError("When creating a Predictor indicator from another indicator, "
                                 "the width of that indicator must be 1. So far, multi-dimensional "
                                 "indicators are not supported yet")
            self._input_data = timelapse
        else:
            raise TypeError("The timelapse must be either a Source or an Indicator")

        # Then, set the predictor instance.
        if not isinstance(algorithm, PredictorAlgorithm) or type(algorithm) == PredictorAlgorithm:
            raise TypeError("The algorithm must be specified and it must be of a strict "
                            "subclass of PredictorAlgorithm")
        self._algorithm = algorithm

        # Finally, the moving STDERR tail size.
        if isinstance(moving_stderr_tail_size, int):
            if moving_stderr_tail_size < 2:
                raise ValueError("The moving standard error tail size must be >= 2")
            if moving_stderr_tail_size < 10:
                warnings.warn("A too small standard deviation tail size was chosen. This will "
                              "work but you might find results less accurate")
        else:
            raise TypeError("The moving standard error tail size must be an integer")
        self._moving_stderr_tail_size = moving_stderr_tail_size
        super().__init__(timelapse, chunk_size=chunk_size)

    @property
    def input_data(self):
        return self._input_data

    def _initial_width(self):
        """
        The initial width for the indicator involves columns:
        - The vector for the prediction.
        - The vector for the structural error for the moment the prediction was done for.
        - The difference between the actual value and the prediction.
        - The standard deviation, taking a proper tail, considering prediction-actual.
        """

        return 4

    def _update(self, start, end):
        """
        Performs a full update, carefully following all the steps.
        :param start: The start position to update.
        :param end: The end (not included) position to update.
        """

        for index in range(start, end):
            self._update_index(index)

    def _update_index(self, index):
        """
        Performs a per-index update, carefully following all the steps.
        :param index: The index being updated.
        """

        # 1. First, take a tail of data. The tail will end
        #    in the given index. If the index is < the tail
        #    size, we'll do nothing at all here.
        if index < self.prediction_tail_size:
            return
        tail = self._input_data[index + 1 - self.prediction_tail_size:index + 1]
        prediction, structural_error = self._algorithm.predict(tail)
        step = self.step
        # 2. Store the prediction in the array (at time {index + step}), at column PREDICTION.
        self._put_value(prediction, index + step, column=self.Columns.PREDICTION)
        # 3. Store the str. error in the array (at time {index + step}), at column STRUCTURAL_ERROR.
        self._put_value(structural_error, index + step, column=self.Columns.STRUCTURAL_ERROR)
        # 4. Store the difference at time {index}, at column PREDICTION_DIFFERENCE. Value:
        #    (self._data[index, PREDICTION] - self._input_data[index]).
        #    It will be NaN if either value is NaN.
        self._put_value(
            self._data[index][self.Columns.PREDICTION] - self._input_data[index],
            index, column=self.Columns.PREDICTION_DIFFERENCE
        )
        # 5. If there's an actual value in the prediction, then train it.
        if not numpy.isnan(self._data[index][self.Columns.PREDICTION]):
            x = self._input_data[index - (self.prediction_tail_size - 1) - step:index + 1 - step]
            self._algorithm.online_train(x, self._input_data[index])
        # 6. Store the standard error at time {index}, at column STANDARD_ERROR. Value:
        #    if there are at least (moving_stderr_tail_size) elements in the tail:
        #        diffs = self._data[index - moving_stderr_tail_size + 1:index + 1]
        #        variance = (diffs ** 2).sum() / (moving_stderr_tail_size - 1)
        #        self._data[index, STANDARD_ERROR] = sqrt(variance)
        #        if any of these values is NaN, this value will be indeed NaN.
        #    otherwise, let it be NaN as default.
        if index >= self._moving_stderr_tail_size - 1:
            moving_stderr_tail = self._data[
                index - self._moving_stderr_tail_size + 1:index + 1
            ][self.Columns.PREDICTION_DIFFERENCE]
            self._put_value(
                (moving_stderr_tail ** 2).sum() / (self._moving_stderr_tail_size - 1),
                index, column=self.Columns.STANDARD_ERROR
            )

    def _window_from_future(self, item):
        """
        Takes a current window (which can be: an integer, a date,
        or a slice) and gets one that belongs to the future. This
        allows making use of a window that belongs to LATER moments,
        rather than the moments being deemed as "current" in the
        given item.
        :param item: The item.
        :return: The translated (future) item.
        """

        if isinstance(item, int):
            return item + self.step
        if isinstance(item, datetime.datetime):
            return item + datetime.timedelta(seconds=int(self.interval) * self.step)
        if isinstance(item, slice):
            start = item.start
            stop = item.stop
            step = item.step
            return slice(
                self._window_from_future(start),
                self._window_from_future(stop),
                step
            )

    def _get_column_data(self, item, column, when_computed: bool = False):
        """
        Gets the data from a given column for this indicator.
        :param item: The item to get.
        :param column: The column to get the data from.
        :param when_computed: If true, the points will be given
            at the time they were produced, rather than at their
            target time.
        :return: The data.
        """

        return self[self._window_from_future(item) if when_computed else item][:, column]

    def get_prediction(self, item, when_computed: bool = False):
        """
        Gets the prediction for this indicator.
        :param item: The item to get.
        :param when_computed: If true, the points will be given
            at the time they were produced, rather than at their
            prediction time.
        :return: The prediction data.
        """

        return self._get_column_data(item, self.Columns.PREDICTION, when_computed)

    def get_structural_error(self, item, when_computed: bool = False):
        """
        Gets the structural error for this indicator.
        :param item: The item to get.
        :param when_computed: If true, the points will be given
            at the time they were produced, rather than at their
            prediction time.
        :return: The structural error data.
        """

        return self._get_column_data(item, self.Columns.STRUCTURAL_ERROR, when_computed)

    def get_prediction_difference(self, item):
        """
        Gets the prediction difference for this indicator.
        :param item: The item to get.
        :return: The prediction difference data.
        """

        return self._get_column_data(item, self.Columns.PREDICTION_DIFFERENCE)

    def get_trailing_standard_error(self, item):
        """
        Gets the trailing standard error for this indicator.
        :param item: The item to get.
        :return: The trailing standard error data.
        """

        return self._get_column_data(item, self.Columns.STANDARD_ERROR)

    @property
    def prediction_tail_size(self):
        """
        The underlying tail size, according to the algorithm.
        """

        return self._algorithm.tail_size

    @property
    def moving_stderr_tail_size(self):
        """
        The underlying tail size for standard error calculation.
        """

        return self._moving_stderr_tail_size

    @property
    def step(self):
        """
        The distance between the time of the last sample and the
        time, in the future, being predicted.
        """

        return self._algorithm.step
