# LSTM for sequence classification in the IMDB dataset
import numpy
from keras.datasets import imdb
from keras.models import Sequential, Model
from keras.layers import Dense, TimeDistributed, Flatten
from keras.layers import LSTM, Input, Dropout, MaxPooling1D, Conv1D
from keras.layers.embeddings import Embedding
from keras.preprocessing import sequence
from keras.callbacks import ModelCheckpoint, ReduceLROnPlateau
from keras import *
from keras.layers import *
from keras import regularizers
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from keras.preprocessing import image
from keras.models import Model
from keras.layers import Input, Dense
from keras.optimizers import SGD, RMSprop, Adam
from keras.callbacks import LearningRateScheduler, TensorBoard
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import GradientBoostingClassifier

# fix random seed for reproducibility
filepath="cnn2para.hdf5"
checkpoint = ModelCheckpoint(filepath, monitor='val_acc', verbose=1, save_best_only=True, mode='max')
learning_rate_reduction = ReduceLROnPlateau(monitor='acc',
                                            patience=5,
                                            verbose=1,
                                            factor=0.5,
                                            min_lr=0.00001)
numpy.random.seed(7)
df_train = pd.read_csv("train.csv",header=None,delimiter=',',dtype='float64',names=list(range(4096))).fillna(0)
X_train = df_train.get_values()
df_label = pd.read_csv("train_label.csv",delimiter=',')
Y_train = df_label['category'].get_values()
Y_train = Y_train.reshape(-1,1)


# load the dataset but only keep the top n words, zero the rest
top_words = 256
# (X_train, y_train), (X_test, y_test) = imdb.load_data(nb_words=top_words)
# truncate and pad input sequences
max_review_length = 4096
X_train_2 =X_train #sequence.pad_sequences(X_train, maxlen=max_review_length, padding='post', truncating="post")
#X_test_2 = X_test#sequence.pad_sequences(X_test, maxlen=max_review_length, padding='post', truncating="post")
# create the model
embedding_vecor_length = 8
x = Input(shape = (max_review_length, ))
y = Embedding(top_words, embedding_vecor_length, input_length=max_review_length)(x)
# model.add(TimeDistributed(1000, input_shape=(max_review_length,)))
# model.add(LSTM(100, return_sequences=True, input_shape = (max_review_length, 1)))
y = Conv1D(filters=128, kernel_size=2, padding='valid', activation='relu')(y)
y = MaxPooling1D(pool_size=2)(y)
y = Dropout(0.5)(y)
y = Conv1D(filters=64, kernel_size=2, padding='valid', activation='relu')(y)
y = MaxPooling1D(pool_size=2)(y)
y = Dropout(0.5)(y)

y = Flatten()(y)
y = Dense(128, activation='relu')(y)
# y = Dropout(0.5)(y)
y = Dense(1, activation='sigmoid')(y)
model = Model(inputs=x, outputs=y)
model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['mse', 'accuracy'])
print(model.summary())
model.fit(X_train_2, Y_train, nb_epoch=30,
          batch_size=512, verbose=1, callbacks = [checkpoint, learning_rate_reduction])
# Final evaluation of the model
X_test = pd.read_csv("test.csv",header=None,delimiter=',',dtype='float64',names=list(range(4096))).fillna(0)
y=model.predict(X_test, batch_size=None, verbose=0, steps=None)
prediction = pd.DataFrame({'malware': y[:,0]})
prediction.to_csv('prediction_cnn.csv', index=True,header=True)
# print(y.shape[0])

# s=np.arange(y.shape[0])
# a= np.zeros((y.shape[0],2))
# a= np.vstack([s,y.reshape(-1)])
# print(a.T)
# np.savetxt("out.csv", a.T, delimiter=',', fmt='%d', header="sample_id,category", comments="")
# print("finish")
