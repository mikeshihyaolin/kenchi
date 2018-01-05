from itertools import combinations

import numpy as np
from sklearn import neighbors
from sklearn.externals.joblib import delayed, Parallel
from sklearn.utils import gen_even_slices

from .base import BaseDetector, OneDimArray, TwoDimArray

__all__ = ['FastABOD']


def _abof(
    X_train: TwoDimArray, X: TwoDimArray, ind: TwoDimArray
) -> OneDimArray:
    """Compute the angle-based outlier factor for each sample."""

    with np.errstate(invalid='raise'):
        return np.var([[
            (pa @ pb) / (pa @ pa) / (pb @ pb) for pa, pb in combinations(
                X_train[ind_p] - p, 2
            )
        ] for p, ind_p in zip(X, ind)], axis=1)


class FastABOD(BaseDetector):
    """Fast Angle-Based Outlier Detector (FastABOD).

    Parameters
    ----------
    fpr : float, default 0.01
        False positive rate. Used to compute the threshold.

    n_jobs : int, default 1
        Number of jobs to run in parallel. If -1, then the number of jobs is
        set to the number of CPU cores.

    kwargs : dict
        All other keyword arguments are passed to neighbors.NearestNeighbors().

    Attributes
    ----------
    threshold_ : float
        Threshold.

    X_ : array-like of shape (n_samples, n_features)
        Training data.

    References
    ----------
    H.-P. Kriegel, M. Schubert and A. Zimek,
    "Angle-based outlier detection in high-dimensional data,"
    In Proceedings of SIGKDD'08, pp. 444-452, 2008.
    """

    @property
    def X_(self) -> OneDimArray:
        return self._knn._fit_X

    def __init__(self, fpr: float = 0.01, n_jobs: int = 1, **kwargs) -> None:
        self.fpr    = fpr
        self.n_jobs = n_jobs
        self._knn   = neighbors.NearestNeighbors(**kwargs)

        self.check_params()

    def check_params(self) -> None:
        """Check validity of parameters and raise ValueError if not valid."""

        if self.fpr < 0. or self.fpr > 1.:
            raise ValueError(
                f'fpr must be between 0.0 and 1.0 inclusive but was {self.fpr}'
            )

    def fit(self, X: TwoDimArray, y: OneDimArray = None) -> 'FastABOD':
        """Fit the model according to the given training data.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.

        y : ignored

        Returns
        -------
        self : FastABOD
            Return self.
        """

        self._knn.fit(X)

        anomaly_score   = self.anomaly_score()
        self.threshold_ = np.percentile(anomaly_score, 100. * (1. - self.fpr))

        return self

    def anomaly_score(self, X: TwoDimArray = None) -> OneDimArray:
        """Compute the anomaly score for each sample.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features), default None
            Data.

        Returns
        -------
        anomaly_score : array-like of shape (n_samples,)
            Anomaly score for each sample.
        """

        ind          = self._knn.kneighbors(X, return_distance=False)

        if X is None:
            X        = self.X_

        n_samples, _ = X.shape

        try:
            result   = Parallel(self.n_jobs)(
                delayed(_abof)(
                    self.X_, X[s], ind[s]
                ) for s in gen_even_slices(n_samples, self.n_jobs)
            )
        except FloatingPointError as e:
            raise ValueError('X must not contain training samples') from e

        return -np.concatenate(result)

    def score(X: TwoDimArray, y: OneDimArray = None) -> float:
        """Compute the mean log-likelihood of the given data."""

        raise NotImplementedError()