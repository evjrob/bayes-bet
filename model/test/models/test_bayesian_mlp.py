import pytest
import numpy as np
from scipy import sparse
from sklearn.utils.estimator_checks import check_estimator
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import NotFittedError
from bayesbet.models.bayesian_mlp import BayesianMLPClassifier

# Suppress a very specific and inconsequential scikit-learn warning
pytestmark = pytest.mark.filterwarnings(
    "ignore:Can't check dok sparse matrix for nan or inf.:UserWarning"
)


@pytest.fixture
def simple_dataset():
    X = np.array([[0, 0], [1, 1], [1, 0], [0, 1]])
    y = np.array([0, 1, 1, 0])
    return X, y


def test_init():
    clf = BayesianMLPClassifier()
    assert clf.hidden_layer_sizes == (100,)

    clf = BayesianMLPClassifier(hidden_layer_sizes=(50, 25))
    assert clf.hidden_layer_sizes == (50, 25)


def test_fit(simple_dataset):
    X, y = simple_dataset
    clf = BayesianMLPClassifier(num_warmup=10, num_samples=10)
    assert clf.fit(X, y) is clf
    assert hasattr(clf, "classes_")
    assert hasattr(clf, "n_classes_")
    assert hasattr(clf, "n_features_in_")


def test_predict(simple_dataset):
    X, y = simple_dataset
    clf = BayesianMLPClassifier(num_warmup=10, num_samples=10)
    clf.fit(X, y)
    predictions = clf.predict(X)
    assert predictions.shape == (4,)
    assert np.all(np.isin(predictions, clf.classes_))


def test_predict_proba(simple_dataset):
    X, y = simple_dataset
    clf = BayesianMLPClassifier(num_warmup=10, num_samples=10)
    clf.fit(X, y)
    probas = clf.predict_proba(X)
    assert probas.shape == (4, 2)
    assert np.allclose(np.sum(probas, axis=1), 1.0)


def test_sparse_input():
    X = sparse.csr_matrix([[0, 0], [1, 1], [1, 0], [0, 1]])
    y = np.array([0, 1, 1, 0])
    clf = BayesianMLPClassifier(num_warmup=10, num_samples=10)
    clf.fit(X, y)
    clf.predict(X)


def test_consistency():
    X = np.random.randn(20, 5)
    y = np.random.randint(0, 2, 20)
    clf1 = BayesianMLPClassifier(num_warmup=10, num_samples=10)
    clf2 = BayesianMLPClassifier(num_warmup=10, num_samples=10)
    clf1.fit(X, y, random_state=42)
    clf2.fit(X, y, random_state=42)
    assert np.allclose(clf1.predict_proba(X), clf2.predict_proba(X))
    assert np.all(clf1.predict(X) == clf2.predict(X))


def test_error_handling():
    clf = BayesianMLPClassifier()
    X = np.array([[0, 0], [1, 1]])
    with pytest.raises(NotFittedError):
        clf.predict(X)


def test_sklearn_compatibility():
    X = np.random.randn(100, 5)
    y = np.random.randint(0, 2, 100)
    clf = BayesianMLPClassifier(num_warmup=10, num_samples=10)
    scores = cross_val_score(clf, X, y, cv=3)
    assert len(scores) == 3

    pipe = make_pipeline(StandardScaler(), clf)
    pipe.fit(X, y)
    pipe.predict(X)


def test_estimator_checks():
    check_estimator(BayesianMLPClassifier())
