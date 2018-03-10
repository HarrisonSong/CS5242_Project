from sklearn.neural_network import MLPClassifier
import pandas as pd
import numpy as np

X = pd.read_csv('train.csv',header=None,dtype='float',names=list(range(4096))).fillna(0)
test = pd.read_csv('test.csv',header=None,dtype='float',names=list(range(4096))).fillna(0)
y = pd.read_csv('train_label.csv')['category']

param = {'solver': 'adam', 'learning_rate_init': 0.001, 'learning_rate': 'invscaling'}
label = "adam"
max_iter = 400

print("MLP training: %s" % label)
mlp = MLPClassifier(verbose=1, batch_size=20, random_state=0,
                    max_iter=max_iter, **param)
mlp.fit(X, y)
print(label)
print("MLP Training set score: %f" % mlp.score(X, y))
print("MLP Training set loss: %f" % mlp.loss_)

# ax.plot(mlp.loss_curve_, label=label, **args)
