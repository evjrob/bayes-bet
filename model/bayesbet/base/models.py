import numpy as np
import jax
import jax.numpy as jnp
from flax import linen as nn
from sklearn.base import clone, BaseEstimator, ClassifierMixin
from sklearn.utils.validation import check_X_y, check_array
from sklearn.preprocessing import LabelEncoder
from sklearn.exceptions import NotFittedError
import blackjax
from blackjax.sgmcmc.gradients import grad_estimator
from tqdm import tqdm
from scipy import sparse
from sklearn.utils.multiclass import type_of_target

# Use 64-bit precision
jax.config.update("jax_enable_x64", True)


class NN(nn.Module):
    hidden_layer_sizes: tuple
    n_classes: int

    @nn.compact
    def __call__(self, x):
        for hidden_size in self.hidden_layer_sizes:
            x = nn.Dense(features=hidden_size)(x)
            x = nn.relu(x)
        x = nn.Dense(features=self.n_classes)(x)
        return nn.log_softmax(x)


class BayesianMLPClassifier(BaseEstimator, ClassifierMixin):
    def __init__(
        self,
        hidden_layer_sizes=(100,),
        num_warmup=1000,
        num_samples=1000,
        batch_size=512,
        step_size=1e-2,
        show_progress=False,
    ):
        self.hidden_layer_sizes = hidden_layer_sizes
        self.num_warmup = num_warmup
        self.num_samples = num_samples
        self.batch_size = batch_size
        self.step_size = step_size
        self.show_progress = show_progress

    def _logprior_fn(self, params):
        leaves, _ = jax.tree_util.tree_flatten(params)
        flat_params = jnp.concatenate([jnp.ravel(a) for a in leaves])
        return jnp.sum(jax.scipy.stats.norm.logpdf(flat_params))

    def _loglikelihood_fn(self, params, data):
        X, y = data
        return jnp.sum(y * self.model_.apply(params, X))

    def _to_dense(self, X):
        if np.iscomplexobj(X):
            raise ValueError("Complex data not supported")
        if sparse.issparse(X):
            X = X.toarray()
        X = np.asarray(X)
        if X.dtype == object:
            X = X.astype(float)
        return X

    def fit(self, X, y, random_state=0):
        # Check that X and y have correct shape
        X, y = check_X_y(X, y, accept_sparse=True, dtype=None)

        # Add this check for classification target
        if type_of_target(y) not in ["binary", "multiclass"]:
            raise ValueError(f"Unknown label type: {type_of_target(y)}")

        X = self._to_dense(X)

        # Initialize and fit the label encoder
        self._label_encoder = LabelEncoder()
        y_encoded = self._label_encoder.fit_transform(y)

        if len(X) == 0 or len(y_encoded) == 0:
            raise ValueError("Cannot fit model with empty dataset")

        # Store the classes seen during fit
        self.classes_ = self._label_encoder.classes_
        self.n_classes_ = len(self.classes_)
        self.n_features_in_ = X.shape[1]

        self.model_ = NN(
            hidden_layer_sizes=self.hidden_layer_sizes, n_classes=self.n_classes_
        )

        # One-hot encode y
        y_onehot = jax.nn.one_hot(y_encoded, self.n_classes_)

        # Initialize model parameters
        rng_key = jax.random.PRNGKey(random_state)
        self.params_ = self.model_.init(rng_key, jnp.ones((1, self.n_features_in_)))

        # Prepare SGLD
        grad_fn = grad_estimator(self._logprior_fn, self._loglikelihood_fn, X.shape[0])
        sgld = blackjax.sgld(grad_fn)

        # Include progress bar if requested
        iterations = range(self.num_warmup + self.num_samples)
        if self.show_progress:
            iterations = tqdm(iterations)

        # Training loop
        for _ in iterations:
            rng_key, sample_key = jax.random.split(rng_key)
            batch_indices = jax.random.choice(
                sample_key, X.shape[0], (self.batch_size,)
            )
            batch = (X[batch_indices], y_onehot[batch_indices])
            self.params_ = jax.jit(sgld.step)(
                sample_key, self.params_, batch, self.step_size / X.shape[0]
            )

        return self

    def predict_proba(self, X):
        self._check_is_fitted()
        X = self._to_dense(check_array(X, accept_sparse=True))

        if X.shape[1] != self.n_features_in_:
            raise ValueError(
                f"X has {X.shape[1]} features, but BayesianMLPClassifier is expecting {self.n_features_in_} features as input."
            )

        return jnp.exp(self.model_.apply(self.params_, X))

    def predict(self, X):
        proba = self.predict_proba(X)
        return self._label_encoder.inverse_transform(np.argmax(proba, axis=1))

    def _check_is_fitted(self):
        attributes = ["classes_", "n_classes_", "n_features_in_", "model_", "params_"]
        if not all(hasattr(self, attr) for attr in attributes):
            raise NotFittedError(
                "This BayesianMLPClassifier instance is not fitted yet. "
                "Call 'fit' with appropriate arguments before using this estimator."
            )

class MappedClassifier(BaseEstimator, ClassifierMixin):
    # A model class that partitions and maps the shots data by the number of skaters on
    # the ice for each team at the time of the shot, including goal-tending (empty net
    # situations). A unique model instance with the specified classifier type is trained
    # for each partition and applied at prediction time. If a partition has not been
    # seen during training, the model will apply a naive prediction corresponding to the
    # closest existing partition key.
    def __init__(self, partition_columns, base_estimator, minimum_partition_size=100):
        self.base_estimator = base_estimator
        self.partition_columns = partition_columns
        self.minimum_partition_size = minimum_partition_size

    @staticmethod
    def _fit_partition(partition, X, y, partition_columns, base_estimator):
        partition_index = [x == partition for x in X[partition_columns].itertuples(index=False, name=None)]
        partition_X = X[partition_index]
        partition_y = y[partition_index]
        return clone(base_estimator).fit(partition_X, partition_y)


    def fit(self, X, y):
        self.estimators = {}
        # Initialize and fit the label encoder
        self._label_encoder = LabelEncoder()
        y_encoded = self._label_encoder.fit_transform(y)

        if len(X) == 0 or len(y_encoded) == 0:
            raise ValueError("Cannot fit model with empty dataset")

        # Store the classes seen during fit
        self.classes_ = self._label_encoder.classes_
        self.n_classes_ = len(self.classes_)
        self.n_features_in_ = X.shape[1]
        
        # Get all unique partitions and their sizes
        partition_counts = X[self.partition_columns].value_counts()
        valid_partitions = [
            tuple(idx) for idx, count in partition_counts.items() 
            if count >= self.minimum_partition_size
        ]
        
        if not valid_partitions:
            raise ValueError(f"No partitions found with at least {self.minimum_partition_size} samples")

        for partition in tqdm(valid_partitions):
            self.estimators[partition] = self._fit_partition(
                partition, X, y, self.partition_columns, self.base_estimator
            )

        return self
    
    def closest_partition(self, partition_key):
        # Return the partition key with the smallest distance to the input key,
        # preferring sequential minimization over key elements in the order of the
        # partition_columns
        if partition_key in self.estimators:
            return partition_key
         
        partition_keys = list(self.estimators.keys())
        for i in range(len(partition_key)): 
            index_distances = [abs(key[i] - partition_key[i]) for key in partition_keys]
            min_index_distance = min(index_distances)
            partition_keys = [
                key for key in partition_keys
                if abs(key[i] - partition_key[i]) == min_index_distance
            ]
        closest_partition_key = partition_keys[-1]
        return closest_partition_key

    def predict_proba(self, X):
        # Create an array to store predictions with same length as X
        predictions = np.zeros((len(X), 2))
        
        # For each partition
        partitions = list(X[self.partition_columns].drop_duplicates().itertuples(index=False, name=None))
        for partition in partitions:
            # Create boolean mask for this partition
            mask = [x == partition for x in X[self.partition_columns].itertuples(index=False, name=None)]
            
            # Get predictions for this partition
            partition_preds = self.estimators[self.closest_partition(partition)].predict_proba(X[mask])
            
            # Store predictions in the correct positions using the mask
            predictions[mask] = partition_preds
        
        return predictions
    
    def predict(self, X):
        proba = self.predict_proba(X)
        return self._label_encoder.inverse_transform(np.argmax(proba, axis=1))

    def _check_is_fitted(self):
        attributes = ["classes_", "n_classes_", "n_features_in_", "model_", "params_"]
        if not all(hasattr(self, attr) for attr in attributes):
            raise NotFittedError(
                "This BayesianMLPClassifier instance is not fitted yet. "
                "Call 'fit' with appropriate arguments before using this estimator."
            )

