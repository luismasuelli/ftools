from numpy import NaN
from ...growing_arrays import GrowingArray


class PredictorMixin:
    """
    Predictor indicators are, in the end, one kind of "useful" indicators.
      These indicators aim to be precise regarding the information they
      provide: literally the future price at certain (future) instant.

    To do so, they contain their own growing array and a forecast size
      >= 1: A prediction made for time t will be stored at slot t+F,
      where F is the forecast size, also an integer value.

    To get one of those predicted values, just call get_predicted(time),
      which takes a future time or a future time slice (this means: t+F
      was already called for those instants). Specifying a time lower
      than F will return NaN, while a time greater than or equal to the
      length of the array will raise an IndexError, and the same will
      occur if the time is lower than 0. F is the forecast size.

    To get one of those predictions (the predicted values before they
      occur) just call get_predictions(time) instead, which is like the
      previous get_predicted functions but moving the indices by +F.

    To add a new prediction at index t, which will stored at index t+F,
      make the indicator call _predict(time, value).
    """

    def __init__(self, forecast_size=1):
        if not (isinstance(forecast_size, int) and forecast_size < 0):
            raise ValueError("The forecast size must be a non-negative integer")
        self._forecast_size = forecast_size
        self._predictions = GrowingArray(float, NaN)

    def _predict(self, time, value):
        """
        Adds a new prediction in certain time. The time will be
          fixed to its forecast version by adding the forecast
          size. In that final index, the time will be stored.

        Existing times cannot be overridden: predictions must
          be made in strict futures.
        :param time: The time when the prediction is made.
        :param value: The predicted value.
        """

        final_index = time + self._forecast_size
        length = len(self._predictions)
        if final_index < length:
            raise IndexError("New predictions must be appended in new positions "
                             "- predictions cannot be overridden")
        elif final_index == length:
            self._predictions[final_index] = value
        else:
            self._predictions[final_index - 1] = NaN
            self._predictions[final_index] = value

    def get_predicted(self, time):
        """
        Gets the predictions for a specific time, which
          may be an integer or a slice.
        :param time: The instant or slice to get the predictions
          at.
        :return: A scalar or array of predictions.
        """

        return self._predictions[time]

    def get_predictions(self, time):
        """
        Get the predictions made at certain time instant or slice.
        :param time: The instant or slice when the prediction(s)
          were made.
        :return: A scalar or array of predictions.
        """

        if isinstance(time, int):
            time += self._forecast_size
        elif isinstance(time, slice):
            start, stop = time.start, time.stop
            start = (start or 0) + self._forecast_size
            stop = (stop or len(self._predictions)) + self._forecast_size
            time = slice(start, stop, 1)
        return self._predictions[time]
