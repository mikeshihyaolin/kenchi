import numpy as np
from sklearn.neighbors import DistanceMetric, NearestNeighbors
from sklearn.utils import check_array, check_random_state
from sklearn.utils.validation import check_is_fitted

from ..base import BaseOutlierDetector

__all__ = ['KNN', 'OneTimeSampling']


class KNN(BaseOutlierDetector):
    """Outlier detector using k-nearest neighbors algorithm.

    Parameters
    ----------
    algorithm : str, default 'auto'
        Tree algorithm to use. Valid algorithms are
        ['kd_tree'|'ball_tree'|'auto'].

    contamination : float, default 0.01
        Proportion of outliers in the data set. Used to define the threshold.

    leaf_size : int, default 30
        Leaf size of the underlying tree.

    metric : str or callable, default 'minkowski'
        Distance metric to use.

    n_jobs : int, default 1
        Number of jobs to run in parallel. If -1, then the number of jobs is
        set to the number of CPU cores.

    n_neighbors : int, default 5
        Number of neighbors.

    p : int, default 2
        Power parameter for the Minkowski metric.

    verbose : bool, default False
        Enable verbose output.

    weight : bool, default False
        If True, anomaly score is the sum of the distances from k nearest
        neighbors.

    metric_params : dict, default None
        Additioal parameters passed to the requested metric.

    Attributes
    ----------
    anomaly_score_ : array-like of shape (n_samples,)
        Anomaly score for each training data.

    fit_time_ : float
        Time spent for fitting in seconds.

    threshold_ : float
        Threshold.

    X_ : array-like of shape (n_samples, n_features)
        Training data.

    References
    ----------
    S. Ramaswamy, R. Rastogi and K. Shim,
    "Efficient algorithms for mining outliers from large data sets,"
    In Proceedings of SIGMOD'00, pp. 427-438, 2000.

    F. Angiulli and C. Pizzuti,
    "Fast outlier detection in high dimensional spaces,"
    In Proceedings of PKDD'02, pp. 15-27, 2002.
    """

    @property
    def X_(self):
        return self._knn._fit_X

    def __init__(
        self,               algorithm='auto',
        contamination=0.01, leaf_size=30,
        metric='minkowski', n_jobs=1,
        n_neighbors=5,      p=2,
        verbose=False,      weight=False,
        metric_params=None
    ):
        super().__init__(contamination=contamination, verbose=verbose)

        self.algorithm     = algorithm
        self.leaf_size     = leaf_size
        self.metric        = metric
        self.n_jobs        = n_jobs
        self.n_neighbors   = n_neighbors
        self.p             = p
        self.weight        = weight
        self.metric_params = metric_params

    def _fit(self, X):
        self._knn           = NearestNeighbors(
            algorithm       = self.algorithm,
            leaf_size       = self.leaf_size,
            metric          = self.metric,
            n_jobs          = self.n_jobs,
            n_neighbors     = self.n_neighbors,
            p               = self.p,
            metric_params   = self.metric_params
        ).fit(X)

        return self

    def anomaly_score(self, X):
        check_is_fitted(self, '_knn')

        X           = check_array(X, estimator=self)

        if np.array_equal(X, self.X_):
            dist, _ = self._knn.kneighbors()
        else:
            dist, _ = self._knn.kneighbors(X)

        if self.weight:
            return np.sum(dist, axis=1)
        else:
            return np.max(dist, axis=1)


class OneTimeSampling(BaseOutlierDetector):
    """One-time sampling.

    Parameters
    ----------
    contamination : float, default 0.01
        Proportion of outliers in the data set. Used to define the threshold.

    metric : str, default 'euclidean'
        Distance metric to use.

    n_samples : int, default 20
        Number of random samples to be used.

    random_state : int, RandomState instance, default None
        Seed of the pseudo random number generator.

    verbose : bool, default False
        Enable verbose output.

    metric_params : dict, default None
        Additional parameters passed to the requested metric.

    Attributes
    ----------
    anomaly_score_ : array-like of shape (n_samples,)
        Anomaly score for each training data.

    fit_time_ : float
        Time spent for fitting in seconds.

    threshold_ : float
        Threshold.

    sampled_ : array-like of shape (n_samples,)
        Indices of subsamples.

    X_ : array-like of shape (n_samples, n_features)
        Training data.

    X_sampled_ : array-like of shape (n_samples, n_features)
        Subset of the given training data.

    References
    ----------
    M. Sugiyama, and K. Borgwardt,
    "Rapid distance-based outlier detection via sampling,"
    Advances in NIPS'13, pp. 467-475, 2013.
    """

    @property
    def X_sampled_(self):
        return self.X_[self.sampled_]

    def __init__(
        self,               contamination=0.01,
        metric='euclidean', n_samples=20,
        random_state=None,  verbose=False,
        metric_params=None
    ):
        super().__init__(contamination=contamination, verbose=verbose)

        self.metric        = metric
        self.n_samples     = n_samples
        self.random_state  = random_state
        self.metric_params = metric_params

    def _check_params(self):
        super()._check_params()

        if self.n_samples <= 0:
            raise ValueError(
                f'n_samples must be positive but was {self.n_samples}'
            )

    def _fit(self, X):
        self.X_             = X
        n_samples, _        = self.X_.shape

        if self.n_samples >= n_samples:
            raise ValueError(
                f'n_samples must be smaller than {n_samples} '
                f'but was {self.n_samples}'
            )

        rnd                 = check_random_state(self.random_state)
        self.sampled_       = rnd.choice(
            n_samples, size=self.n_samples, replace=False
        )

        # sort again as choice does not guarantee sorted order
        self.sampled_       = np.sort(self.sampled_)

        if self.metric_params is None:
            metric_params   = {}
        else:
            metric_params   = self.metric_params

        self._metric        = DistanceMetric.get_metric(
            self.metric, **metric_params
        )

        return self

    def anomaly_score(self, X):
        check_is_fitted(self, '_metric')

        X = check_array(X, estimator=self)

        return np.min(self._metric.pairwise(X, self.X_sampled_), axis=1)
