from matplotlib.axes import Axes
from sklearn.pipeline import Pipeline as SKLearnPipeline
from sklearn.utils.metaestimators import if_delegate_has_method

from .utils import OneDimArray, TwoDimArray

__all__ = ['Pipeline']


class Pipeline(SKLearnPipeline):
    """Pipeline of transforms with a final estimator.

    Parameters
    ----------
    steps : list
        List of (name, transform) tuples (implementing fit/transform) that are
        chained, in the order in which they are chained, with the last object
        an estimator.

    memory : instance of joblib.Memory or string, default None
        Used to cache the fitted transformers of the pipeline. By default, no
        caching is performed. If a string is given, it is the path to the
        caching directory. Enabling caching triggers a clone of the
        transformers before fitting. Therefore, the transformer instance given
        to the pipeline cannot be inspected directly. Use the attribute
        ``named_steps`` or ``steps`` to inspect estimators within the pipeline.
        Caching the transformers is advantageous when fitting is time
        consuming.

    Attributes
    ----------
    named_steps : dict
        Read-only attribute to access any step parameter by user given name.
        Keys are step names and values are steps parameters.
    """

    @if_delegate_has_method(delegate='_final_estimator')
    def anomaly_score(self, X: TwoDimArray = None) -> OneDimArray:
        """Apply transforms, and compute the anomaly score for each sample with
        the final estimator.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features), default None
            Data.

        Returns
        -------
        anomaly_score : array-like of shape (n_samples,)
            Anomaly score for each sample.
        """

        if X is not None:
            for _, transform in self.steps[:-1]:
                if transform is not None:
                    X = transform.transform(X)

        return self._final_estimator.anomaly_score(X)

    @if_delegate_has_method(delegate='_final_estimator')
    def feature_wise_anomaly_score(self, X: TwoDimArray = None) -> TwoDimArray:
        """Apply transforms, and compute the feature-wise anomaly score for
        each sample with the final estimator.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features), default None
            Data.

        Returns
        -------
        anomaly_score : array-like of shape (n_samples, n_features)
            Feature-wise anomaly score for each sample.
        """

        if X is not None:
            for _, transform in self.steps[:-1]:
                if transform is not None:
                    X = transform.transform(X)

        return self._final_estimator.feature_wise_anomaly_score(X)

    @if_delegate_has_method(delegate='_final_estimator')
    def plot_anomaly_score(self, X: TwoDimArray = None, **kwargs) -> Axes:
        """Apply transoforms, and plot the anomaly scores for each sample.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features), default None
            Data.

        **kwargs : dict
            Other keywords.

        Returns
        -------
        ax : matplotlib Axes
            Axes on which the plot was drawn.
        """

        if X is not None:
            for _, transform in self.steps[:-1]:
                if transform is not None:
                    X = transform.transform(X)

        return self._final_estimator.plot_anomaly_score(X, **kwargs)

    @if_delegate_has_method(delegate='_final_estimator')
    def plot_roc_curve(self, X: TwoDimArray, y: OneDimArray, **kwargs) -> Axes:
        """Apply transoforms, and plot the Receiver Operating Characteristic
        (ROC) curve with the final estimator.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data.

        y : array-like of shape (n_samples,)
            Labels.

        **kwargs : dict
            Other keywords.

        Returns
        -------
        ax : matplotlib Axes
            Axes on which the plot was drawn.
        """

        for _, transform in self.steps[:-1]:
            if transform is not None:
                X = transform.transform(X)

        return self._final_estimator.plot_roc_curve(X, y, **kwargs)

    @property
    def plot_partial_corrcoef(self):
        return self._final_estimator.plot_partial_corrcoef
