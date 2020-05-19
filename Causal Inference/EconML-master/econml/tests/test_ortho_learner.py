# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from econml._ortho_learner import _OrthoLearner, _crossfit
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression, LassoCV, Lasso
from sklearn.model_selection import KFold
import numpy as np
import unittest
import joblib
import pytest


class TestOrthoLearner(unittest.TestCase):

    def test_crossfit(self):

        class Wrapper:

            def __init__(self, model):
                self._model = model

            def fit(self, X, y, Q, W=None):
                self._model.fit(X, y)
                return self

            def predict(self, X, y, Q, W=None):
                return self._model.predict(X), y - self._model.predict(X), X

        np.random.seed(123)
        X = np.random.normal(size=(5000, 3))
        y = X[:, 0] + np.random.normal(size=(5000,))
        folds = list(KFold(2).split(X, y))
        model = Lasso(alpha=0.01)
        nuisance, model_list, fitted_inds = _crossfit(Wrapper(model),
                                                      folds,
                                                      X, y, y, W=y, Z=None)
        np.testing.assert_allclose(nuisance[0][folds[0][1]],
                                   model.fit(X[folds[0][0]], y[folds[0][0]]).predict(X[folds[0][1]]))
        np.testing.assert_allclose(nuisance[0][folds[0][0]],
                                   model.fit(X[folds[0][1]], y[folds[0][1]]).predict(X[folds[0][0]]))
        coef_ = np.zeros(X.shape[1])
        coef_[0] = 1
        [np.testing.assert_allclose(coef_, mdl._model.coef_, rtol=0, atol=0.08) for mdl in model_list]
        np.testing.assert_array_equal(fitted_inds, np.arange(X.shape[0]))

        np.random.seed(123)
        X = np.random.normal(size=(5000, 3))
        y = X[:, 0] + np.random.normal(size=(5000,))
        folds = list(KFold(2).split(X, y))
        model = Lasso(alpha=0.01)
        nuisance, model_list, fitted_inds = _crossfit(Wrapper(model),
                                                      folds,
                                                      X, y, None, W=y, Z=None)
        np.testing.assert_allclose(nuisance[0][folds[0][1]],
                                   model.fit(X[folds[0][0]], y[folds[0][0]]).predict(X[folds[0][1]]))
        np.testing.assert_allclose(nuisance[0][folds[0][0]],
                                   model.fit(X[folds[0][1]], y[folds[0][1]]).predict(X[folds[0][0]]))
        coef_ = np.zeros(X.shape[1])
        coef_[0] = 1
        [np.testing.assert_allclose(coef_, mdl._model.coef_, rtol=0, atol=0.08) for mdl in model_list]
        np.testing.assert_array_equal(fitted_inds, np.arange(X.shape[0]))

        np.random.seed(123)
        X = np.random.normal(size=(5000, 3))
        y = X[:, 0] + np.random.normal(size=(5000,))
        folds = list(KFold(2).split(X, y))
        model = Lasso(alpha=0.01)
        nuisance, model_list, fitted_inds = _crossfit(Wrapper(model),
                                                      folds,
                                                      X, y, None, W=None, Z=None)
        np.testing.assert_allclose(nuisance[0][folds[0][1]],
                                   model.fit(X[folds[0][0]], y[folds[0][0]]).predict(X[folds[0][1]]))
        np.testing.assert_allclose(nuisance[0][folds[0][0]],
                                   model.fit(X[folds[0][1]], y[folds[0][1]]).predict(X[folds[0][0]]))
        coef_ = np.zeros(X.shape[1])
        coef_[0] = 1
        [np.testing.assert_allclose(coef_, mdl._model.coef_, rtol=0, atol=0.08) for mdl in model_list]
        np.testing.assert_array_equal(fitted_inds, np.arange(X.shape[0]))

        class Wrapper:

            def __init__(self, model):
                self._model = model

            def fit(self, X, y, W=None):
                self._model.fit(X, y)
                return self

            def predict(self, X, y, W=None):
                return self._model.predict(X), y - self._model.predict(X), X

        np.random.seed(123)
        X = np.random.normal(size=(5000, 3))
        y = X[:, 0] + np.random.normal(size=(5000,))
        folds = [(np.arange(X.shape[0] // 2), np.arange(X.shape[0] // 2, X.shape[0])),
                 (np.arange(X.shape[0] // 2), np.arange(X.shape[0] // 2, X.shape[0]))]
        model = Lasso(alpha=0.01)
        with pytest.raises(AttributeError) as e_info:
            nuisance, model_list, fitted_inds = _crossfit(Wrapper(model),
                                                          folds,
                                                          X, y, W=y, Z=None)

        np.random.seed(123)
        X = np.random.normal(size=(5000, 3))
        y = X[:, 0] + np.random.normal(size=(5000,))
        folds = [(np.arange(X.shape[0]), np.arange(X.shape[0]))]
        model = Lasso(alpha=0.01)
        with pytest.raises(AttributeError) as e_info:
            nuisance, model_list, fitted_inds = _crossfit(Wrapper(model),
                                                          folds,
                                                          X, y, W=y, Z=None)

    def test_ol(self):

        class ModelNuisance:
            def __init__(self, model_t, model_y):
                self._model_t = model_t
                self._model_y = model_y

            def fit(self, Y, T, W=None):
                self._model_t.fit(W, T)
                self._model_y.fit(W, Y)
                return self

            def predict(self, Y, T, W=None):
                return Y - self._model_y.predict(W), T - self._model_t.predict(W)

        class ModelFinal:

            def __init__(self):
                return

            def fit(self, Y, T, W=None, nuisances=None):
                Y_res, T_res = nuisances
                self.model = LinearRegression(fit_intercept=False).fit(T_res.reshape(-1, 1), Y_res)
                return self

            def predict(self, X=None):
                return self.model.coef_[0]

            def score(self, Y, T, W=None, nuisances=None):
                Y_res, T_res = nuisances
                return np.mean((Y_res - self.model.predict(T_res.reshape(-1, 1)))**2)

        np.random.seed(123)
        X = np.random.normal(size=(10000, 3))
        sigma = 0.1
        y = X[:, 0] + X[:, 1] + np.random.normal(0, sigma, size=(10000,))
        est = _OrthoLearner(ModelNuisance(LinearRegression(), LinearRegression()), ModelFinal(),
                            n_splits=2, discrete_treatment=False, discrete_instrument=False, random_state=None)
        est.fit(y, X[:, 0], W=X[:, 1:])
        np.testing.assert_almost_equal(est.const_marginal_effect(), 1, decimal=3)
        np.testing.assert_array_almost_equal(est.effect(), np.ones(1), decimal=3)
        np.testing.assert_array_almost_equal(est.effect(T0=0, T1=10), np.ones(1) * 10, decimal=2)
        np.testing.assert_almost_equal(est.score(y, X[:, 0], W=X[:, 1:]), sigma**2, decimal=3)
        np.testing.assert_almost_equal(est.score_, sigma**2, decimal=3)
        np.testing.assert_almost_equal(est.model_final.model.coef_[0], 1, decimal=3)

        # Test non keyword based calls to fit
        np.random.seed(123)
        X = np.random.normal(size=(10000, 3))
        sigma = 0.1
        y = X[:, 0] + X[:, 1] + np.random.normal(0, sigma, size=(10000,))
        est = _OrthoLearner(ModelNuisance(LinearRegression(), LinearRegression()), ModelFinal(),
                            n_splits=2, discrete_treatment=False, discrete_instrument=False, random_state=None)
        # test non-array inputs
        est.fit(list(y), list(X[:, 0]), None, X[:, 1:])
        np.testing.assert_almost_equal(est.const_marginal_effect(), 1, decimal=3)
        np.testing.assert_array_almost_equal(est.effect(), np.ones(1), decimal=3)
        np.testing.assert_array_almost_equal(est.effect(T0=0, T1=10), np.ones(1) * 10, decimal=2)
        np.testing.assert_almost_equal(est.score(y, X[:, 0], None, X[:, 1:]), sigma**2, decimal=3)
        np.testing.assert_almost_equal(est.score_, sigma**2, decimal=3)
        np.testing.assert_almost_equal(est.model_final.model.coef_[0], 1, decimal=3)

        # Test custom splitter
        np.random.seed(123)
        X = np.random.normal(size=(10000, 3))
        sigma = 0.1
        y = X[:, 0] + X[:, 1] + np.random.normal(0, sigma, size=(10000,))
        est = _OrthoLearner(ModelNuisance(LinearRegression(), LinearRegression()), ModelFinal(),
                            n_splits=KFold(n_splits=3),
                            discrete_treatment=False, discrete_instrument=False, random_state=None)
        est.fit(y, X[:, 0], None, X[:, 1:])
        np.testing.assert_almost_equal(est.const_marginal_effect(), 1, decimal=3)
        np.testing.assert_array_almost_equal(est.effect(), np.ones(1), decimal=3)
        np.testing.assert_array_almost_equal(est.effect(T0=0, T1=10), np.ones(1) * 10, decimal=2)
        np.testing.assert_almost_equal(est.score(y, X[:, 0], W=X[:, 1:]), sigma**2, decimal=3)
        np.testing.assert_almost_equal(est.score_, sigma**2, decimal=3)
        np.testing.assert_almost_equal(est.model_final.model.coef_[0], 1, decimal=3)

        # Test incomplete set of test folds
        np.random.seed(123)
        X = np.random.normal(size=(10000, 3))
        sigma = 0.1
        y = X[:, 0] + X[:, 1] + np.random.normal(0, sigma, size=(10000,))
        folds = [(np.arange(X.shape[0] // 2), np.arange(X.shape[0] // 2, X.shape[0]))]
        est = _OrthoLearner(ModelNuisance(LinearRegression(), LinearRegression()), ModelFinal(),
                            n_splits=KFold(n_splits=3), discrete_treatment=False,
                            discrete_instrument=False, random_state=None)
        est.fit(y, X[:, 0], None, X[:, 1:])
        np.testing.assert_almost_equal(est.const_marginal_effect(), 1, decimal=3)
        np.testing.assert_array_almost_equal(est.effect(), np.ones(1), decimal=3)
        np.testing.assert_array_almost_equal(est.effect(T0=0, T1=10), np.ones(1) * 10, decimal=2)
        np.testing.assert_almost_equal(est.score(y, X[:, 0], W=X[:, 1:]), sigma**2, decimal=3)
        np.testing.assert_almost_equal(est.score_, sigma**2, decimal=3)
        np.testing.assert_almost_equal(est.model_final.model.coef_[0], 1, decimal=3)

    def test_ol_no_score_final(self):
        class ModelNuisance:
            def __init__(self, model_t, model_y):
                self._model_t = model_t
                self._model_y = model_y

            def fit(self, Y, T, W=None):
                self._model_t.fit(W, T)
                self._model_y.fit(W, Y)
                return self

            def predict(self, Y, T, W=None):
                return Y - self._model_y.predict(W), T - self._model_t.predict(W)

        class ModelFinal:

            def __init__(self):
                return

            def fit(self, Y, T, W=None, nuisances=None):
                Y_res, T_res = nuisances
                self.model = LinearRegression(fit_intercept=False).fit(T_res.reshape(-1, 1), Y_res)
                return self

            def predict(self, X=None):
                return self.model.coef_[0]

        np.random.seed(123)
        X = np.random.normal(size=(10000, 3))
        sigma = 0.1
        y = X[:, 0] + X[:, 1] + np.random.normal(0, sigma, size=(10000,))
        est = _OrthoLearner(ModelNuisance(LinearRegression(), LinearRegression()), ModelFinal(),
                            n_splits=2, discrete_treatment=False, discrete_instrument=False, random_state=None)
        est.fit(y, X[:, 0], W=X[:, 1:])
        np.testing.assert_almost_equal(est.const_marginal_effect(), 1, decimal=3)
        np.testing.assert_array_almost_equal(est.effect(), np.ones(1), decimal=3)
        np.testing.assert_array_almost_equal(est.effect(T0=0, T1=10), np.ones(1) * 10, decimal=2)
        assert est.score_ is None
        np.testing.assert_almost_equal(est.model_final.model.coef_[0], 1, decimal=3)

    def test_ol_discrete_treatment(self):
        class ModelNuisance:
            def __init__(self, model_t, model_y):
                self._model_t = model_t
                self._model_y = model_y

            def fit(self, Y, T, W=None):
                self._model_t.fit(W, np.matmul(T, np.arange(1, T.shape[1] + 1)))
                self._model_y.fit(W, Y)
                return self

            def predict(self, Y, T, W=None):
                return Y - self._model_y.predict(W), T - self._model_t.predict_proba(W)[:, 1:]

        class ModelFinal:

            def __init__(self):
                return

            def fit(self, Y, T, W=None, nuisances=None):
                Y_res, T_res = nuisances
                self.model = LinearRegression(fit_intercept=False).fit(T_res.reshape(-1, 1), Y_res)
                return self

            def predict(self):
                # theta needs to be of dimension (1, d_t) if T is (n, d_t)
                return np.array([[self.model.coef_[0]]])

            def score(self, Y, T, W=None, nuisances=None):
                Y_res, T_res = nuisances
                return np.mean((Y_res - self.model.predict(T_res.reshape(-1, 1)))**2)

        np.random.seed(123)
        X = np.random.normal(size=(10000, 3))
        import scipy.special
        from sklearn.linear_model import LogisticRegression
        T = np.random.binomial(1, scipy.special.expit(X[:, 0]))
        sigma = 0.01
        y = T + X[:, 0] + np.random.normal(0, sigma, size=(10000,))
        est = _OrthoLearner(ModelNuisance(LogisticRegression(solver='lbfgs'), LinearRegression()), ModelFinal(),
                            n_splits=2, discrete_treatment=True, discrete_instrument=False, random_state=None)
        est.fit(y, T, W=X)
        np.testing.assert_almost_equal(est.const_marginal_effect(), 1, decimal=3)
        np.testing.assert_array_almost_equal(est.effect(), np.ones(1), decimal=3)
        np.testing.assert_almost_equal(est.score(y, T, W=X), sigma**2, decimal=3)
        np.testing.assert_almost_equal(est.model_final.model.coef_[0], 1, decimal=3)
