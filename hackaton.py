# -*- coding: utf-8 -*-
"""hackaton.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/14kFk5nCSPrpa1Ez2igqUB4DLJaXZazgS

# AutoML

# 1. Data Preprocessing: You'll need to preprocess your data by handling missing values, encoding categorical variables, and normalizing numerical features if necessary.
"""

import pandas as pd
import numpy as np
import os

folder_path = "./data/"

def read_all_files(list_of_file_starters, print_output=False):
    df_dict = {}
    list_of_failed_dfs = []

    for element in list_of_file_starters:
        csv_files = [f for f in os.listdir(folder_path) if f.startswith(element) and not f.endswith("2009.csv")]

        final_df = pd.DataFrame()

        for filename in csv_files:
            if print_output: print(f"reading and loading file: {filename}")
            try:
                df_sub = pd.read_csv(os.path.join(folder_path, filename), encoding='iso-8859-1')
                final_df = pd.concat([final_df, df_sub])
                if print_output: print(len(final_df))
            except pd.errors.ParserError as error:
                list_of_failed_dfs.append(filename)

        df_dict[element] = final_df

    return df_dict, list_of_failed_dfs
    print(list_of_failed_dfs)

dfs, list_of_failed_dfs = read_all_files(["caracteristiques_", "lieux_", "vehicules_", "usagers_"])


for key in dfs:
    print(key)
    print(dfs[key].columns)

merged_df = pd.merge(
    dfs["caracteristiques_"]
    , dfs["lieux_"]
    , on='Num_Acc'
)

merged_df = pd.merge(
    merged_df
    , dfs["vehicules_"]
    , on='Num_Acc'
)

merged_df = pd.merge(
    merged_df
    , dfs["usagers_"]
    , on='Num_Acc'
)

merged_df.head()

merged_df.columns

"""## nettoyage colonnes et lignes"""

merged_df = merged_df[merged_df['num_veh_x'] == merged_df['num_veh_y']]
merged_df = merged_df.drop('num_veh_y', axis=1)

merged_df = merged_df.drop(['Num_Acc', 'num_veh_x'], axis=1)

merged_df = merged_df.drop(['voie', 'v1', 'v2', 'adr', 'lat', 'long'], axis=1)

merged_df = merged_df.drop(['pr', 'env1'], axis=1)

merged_df['hrmn'] = merged_df['hrmn'].astype('str').str[:2].astype('int')

merged_df.head()

merged_df.grav.isnull().sum()

# merged_df.to_csv('hackaton_merged_first_cleaning_csv', sep=';', header=True, index=False)



numerical_columns = ['an', 'mois', 'jour', 'hrmn', 'nbv', 'lartpc', 'larrout', 'an_nais', 'pr1', 'vma', 'occutc']

target_column = 'grav'
categorical_columns = [
    'gps', 'lum', 'agg', 'com'
    , 'int', 'atm', 'col', 'catr'
    , 'circ', 'vosp', 'prof', 'plan'
    , 'surf', 'infra', 'situ', 'senc'
    , 'catv', 'obs', 'obsm', 'choc'
    , 'manv','place', 'catu', 'sexe'
    , 'trajet', 'secu', 'locp', 'actp'
    , 'etatp',
]

merged_df_onehot = pd.get_dummies(merged_df, columns=categorical_columns, dtype=int)
print(merged_df_onehot.columns.shape)
merged_df_onehot.columns.tolist()

merged_df_onehot.shape

columns_witn_na = merged_df_onehot.columns[(merged_df_onehot.isnull().sum() > 0)]
columns_witn_na

def fill_na_w_random_n_missing_value(df):
    import random

    nan_columns = df.columns[(df.isnull().sum() > 0)]
    print(f"nan columns are: {nan_columns}")

    for c in nan_columns:
        c = str(c)
        print(f"treating column: {c}")
        missing_column_name = c + "_missing"

        df[missing_column_name] = 0
        unique_values = df[c].dropna().unique()
        null_indexes = df[df[c].isnull()].index

        for i in null_indexes:
            print(f"beginning state {df.at[i, c]}, {df.at[i, missing_column_name]}")

            df.at[i, c] = random.choice(unique_values)

            df.at[i, missing_column_name] = 1

            print(f"arrival state {df.at[i, c]}, {df.at[i, missing_column_name]}")


    return df

filled_merged_df_onehot = fill_na_w_random_n_missing_value(merged_df_onehot)

filled_merged_df_onehot.head()

filled_merged_df_onehot.to_csv('preprocessed_df.csv', sep=';', header=True, index=False)

filled_merged_df_onehot.shape
filled_merged_df_onehot['grav'].value_counts()

import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any
import tensorflow as tf
import random
from datetime import datetime
import matplotlib.pyplot as plt
import xgboost as xgb

class SimpleAutoML:
    def __init__(self, target_column: str):
        self.target_column = target_column
        self.best_model = None
        self.best_params = None
        self.best_score = float('-inf')
        self.results_history = []
        self.feature_means = None
        self.feature_stds = None

    def normalize_features(self, X: np.ndarray) -> np.ndarray:
        self.feature_means = np.mean(X, axis=0)
        self.feature_stds = np.std(X, axis=0)
        self.feature_stds = np.where(self.feature_stds == 0, 1, self.feature_stds)
        X_normalized = (X - self.feature_means) / self.feature_stds
        return X_normalized

    def load_data(self, filepath: str) -> Tuple[np.ndarray, np.ndarray]:
        df = pd.read_csv(filepath, sep=';')
        df = df.head(2000)

        if self.target_column not in df.columns:
            raise ValueError(f"La colonne cible '{self.target_column}' n'est pas présente dans le dataset")

        y = df[self.target_column]
        X = df.drop(self.target_column, axis=1)

        X = X.to_numpy()
        y = y.to_numpy()

        X = self.normalize_features(X)
        X = np.nan_to_num(X)

        X = X.astype(np.float32)
        y = y.astype(np.int32)

        y = y - np.min(y)

        return X, y

    def train_val_test_split(self, X: np.ndarray, y: np.ndarray, val_ratio: float = 0.2, test_ratio: float = 0.1) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        n = X.shape[0]
        indices = np.arange(n)
        np.random.shuffle(indices)

        test_size = int(n * test_ratio)
        val_size = int(n * val_ratio)

        test_indices = indices[:test_size]
        val_indices = indices[test_size:test_size+val_size]
        train_indices = indices[test_size+val_size:]

        X_test = X[test_indices]
        y_test = y[test_indices]
        X_val = X[val_indices]
        y_val = y[val_indices]
        X_train = X[train_indices]
        y_train = y[train_indices]

        return X_train, y_train, X_val, y_val, X_test, y_test

    def random_architecture(self) -> Dict[str, Any]:
        model_type = 'mlp' if random.random() < 0.8 else 'xgb'

        if model_type == 'mlp':
            return {
                'model_type': 'mlp',
                'n_layers': random.randint(2, 3),
                'neurons_per_layer': [random.choice([32, 64]) for _ in range(3)],
                'activation': 'relu',
                'learning_rate': random.choice([0.001, 0.0001]),
                'batch_size': 32,
                'dropout_rate': 0.2
            }
        else:
            return {
                'model_type': 'xgb',
                'max_depth': random.choice([3, 5, 7]),
                'learning_rate': random.choice([0.1, 0.05, 0.01]),
                'n_estimators': random.choice([50, 100, 200]),
                'subsample': random.choice([0.8, 1.0]),
                'colsample_bytree': random.choice([0.8, 1.0])
            }

    def build_mlp_model(self, input_shape: int, architecture: Dict[str, Any]) -> tf.keras.Model:
        model = tf.keras.Sequential()
        model.add(tf.keras.layers.InputLayer(input_shape=(input_shape,)))
        model.add(tf.keras.layers.Dense(
            architecture['neurons_per_layer'][0],
            activation=architecture['activation']
        ))
        model.add(tf.keras.layers.Dropout(architecture['dropout_rate']))

        for i in range(1, architecture['n_layers']):
            model.add(tf.keras.layers.Dense(
                architecture['neurons_per_layer'][i],
                activation=architecture['activation']
            ))
            model.add(tf.keras.layers.Dropout(architecture['dropout_rate']))

        model.add(tf.keras.layers.Dense(4, activation='softmax'))

        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=architecture['learning_rate']),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        return model

    def calculate_f1_score(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        y_pred_classes = np.argmax(y_pred, axis=1)
        f1_scores = []

        for cls in range(4):
            tp = np.sum((y_true == cls) & (y_pred_classes == cls))
            fp = np.sum((y_true != cls) & (y_pred_classes == cls))
            fn = np.sum((y_true == cls) & (y_pred_classes != cls))

            precision = tp / (tp + fp + 1e-10)
            recall = tp / (tp + fn + 1e-10)
            f1 = 2 * (precision * recall) / (precision + recall + 1e-10)
            f1_scores.append(f1)

        return np.mean(f1_scores)

    def confusion_matrix(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        conf_mat = np.zeros((4,4), dtype=int)
        for t, p in zip(y_true, y_pred):
            conf_mat[t, p] += 1
        return conf_mat

    def plot_confusion_matrix(self, conf_mat: np.ndarray):
        plt.figure(figsize=(6, 6))
        plt.imshow(conf_mat, cmap='Blues')
        plt.title("Matrice de confusion")
        plt.xlabel("Prédit")
        plt.ylabel("Vrai")
        for i in range(4):
            for j in range(4):
                plt.text(j, i, str(conf_mat[i, j]), ha='center', va='center', color='red')
        plt.colorbar()
        plt.show()

    def evaluate_on_test(self, X_test: np.ndarray, y_test: np.ndarray):
        if self.best_model is None:
            print("Aucun modèle trouvé.")
            return

        if self.best_params['model_type'] == 'mlp':
            y_pred_proba = self.best_model.predict(X_test)
        else:
            dtest = xgb.DMatrix(X_test)
            y_pred_proba = self.best_model.predict(dtest)

        y_pred_classes = np.argmax(y_pred_proba, axis=1)

        f1_test = self.calculate_f1_score(y_test, y_pred_proba)
        print(f"F1-score sur test: {f1_test:.4f}")

        conf_mat = self.confusion_matrix(y_test, y_pred_classes)
        self.plot_confusion_matrix(conf_mat)

    def train_and_evaluate_mlp(self, X_train: np.ndarray, y_train: np.ndarray,
                               X_val: np.ndarray, y_val: np.ndarray,
                               architecture: Dict[str, Any]) -> Tuple[float, Any]:
        model = self.build_mlp_model(X_train.shape[1], architecture)
        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        )

        model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=30,
            batch_size=architecture['batch_size'],
            callbacks=[early_stopping],
            verbose=0
        )

        y_val_pred = model.predict(X_val, verbose=0)
        f1_val = self.calculate_f1_score(y_val, y_val_pred)

        return f1_val, model

    def train_and_evaluate_xgb(self, X_train: np.ndarray, y_train: np.ndarray,
                               X_val: np.ndarray, y_val: np.ndarray,
                               architecture: Dict[str, Any]) -> Tuple[float, Any]:
        params = {
            'objective': 'multi:softprob',
            'num_class': 4,
            'max_depth': architecture['max_depth'],
            'learning_rate': architecture['learning_rate'],
            'subsample': architecture['subsample'],
            'colsample_bytree': architecture['colsample_bytree'],
            'eval_metric': 'mlogloss'
        }
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dval = xgb.DMatrix(X_val, label=y_val)

        evals = [(dtrain, 'train'), (dval, 'eval')]
        model = xgb.train(params, dtrain, num_boost_round=architecture['n_estimators'], evals=evals,
                          early_stopping_rounds=10, verbose_eval=False)

        y_val_pred = model.predict(dval)
        f1_val = self.calculate_f1_score(y_val, y_val_pred)

        return f1_val, model

    def train_and_evaluate(self, X_train: np.ndarray, y_train: np.ndarray,
                           X_val: np.ndarray, y_val: np.ndarray,
                           architecture: Dict[str, Any]) -> Tuple[float, Any]:
        if architecture['model_type'] == 'mlp':
            return self.train_and_evaluate_mlp(X_train, y_train, X_val, y_val, architecture)
        else:
            return self.train_and_evaluate_xgb(X_train, y_train, X_val, y_val, architecture)

    def search(self, X: np.ndarray, y: np.ndarray, n_trials: int = 20):
        print("Début de la recherche d'architecture")
        print(f"Shape des données - X: {X.shape}, y: {y.shape}")
        print(f"Classes uniques dans y: {np.unique(y)}")

        X_train, y_train, X_val, y_val, self.X_test, self.y_test = self.train_val_test_split(X, y, val_ratio=0.2, test_ratio=0.1)

        for trial in range(n_trials):
            print(f"\nEssai {trial + 1}/{n_trials}")
            architecture = self.random_architecture()
            print("Architecture testée:", architecture)

            score, model = self.train_and_evaluate(X_train, y_train, X_val, y_val, architecture)
            self.results_history.append((trial+1, architecture, score))

            print(f"Score F1 obtenu sur val: {score:.4f}")
            if score > self.best_score:
                self.best_score = score
                self.best_model = model
                self.best_params = architecture
                print(f"Nouveau meilleur score: {score:.4f} avec {architecture}")

    def plot_trials_performance(self):
        trials = [r[0] for r in self.results_history]
        scores = [r[2] for r in self.results_history]

        plt.figure(figsize=(8, 5))
        plt.plot(trials, scores, marker='o')
        plt.title("Évolution du F1-score sur validation au fil des essais")
        plt.xlabel("Numéro d'essai")
        plt.ylabel("F1-score")
        plt.grid(True)
        plt.show()

if __name__ == "__main__":
    automl = SimpleAutoML(target_column='grav')
    X, y = automl.load_data('preprocessed_dfc_1.csv')

    automl.search(X, y, n_trials=5)
    automl.plot_trials_performance()

    automl.evaluate_on_test(automl.X_test, automl.y_test)