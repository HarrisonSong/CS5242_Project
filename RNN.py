from keras.layers import Embedding, ELU, Dropout, Flatten, Input, Dense, BatchNormalization, Conv1D, MaxPooling1D, LSTM, CuDNNLSTM
from keras.layers import concatenate, multiply, Bidirectional
from keras.models import Sequential
from keras.layers import TimeDistributed, Reshape, RepeatVector, Lambda, Activation
from keras.regularizers import l2, l1_l2
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping
from keras.utils.np_utils import to_categorical
from keras import backend as K
from keras import Model
from keras.callbacks import LearningRateScheduler

import pandas as pd
import numpy as np

data = pd.read_csv('train.csv',header=None,dtype='float',names=list(range(4096)))
test = pd.read_csv('test.csv',header=None,dtype='float',names=list(range(4096)))
label = pd.read_csv('train_label.csv')['category'].values.reshape(-1, 1)


maxlen=4096
embed_size=96
lstm_layer_size = 100
num_layers = 1

model = Sequential()
model.add(Embedding(256, embed_size, input_length=maxlen, embeddings_regularizer=l2(1e-4)))
model.add(Dropout(0.2))

for l in range(0, num_layers - 1):
  model.add(CuDNNLSTM(lstm_layer_size, kernel_regularizer=l2(1e-5), recurrent_regularizer=l2(1e-5), return_sequences=True))
  model.add(Dropout(0.5))
model.add(CuDNNLSTM(lstm_layer_size, kernel_regularizer=l2(1e-5), recurrent_regularizer=l2(1e-5), return_sequences=True))
model.add(Dropout(0.5))

model.add(Flatten())
model.add(Dense(1, activation='sigmoid', name='loss_out'))

def scheduler(epoch):
    if epoch%1==0 and epoch!=0:
        lr = K.get_value(model.optimizer.lr)
        K.set_value(model.optimizer.lr, lr*.5)
        print("lr changed to {}".format(lr*.5))
    return K.get_value(model.optimizer.lr)

lr_decay = LearningRateScheduler(scheduler)

optimizer = Adam(lr=0.004, clipnorm=1.0)
model.compile(optimizer, loss='binary_crossentropy', metrics=['binary_accuracy'])

es = EarlyStopping(monitor='binary_accuracy', min_delta=0, patience=0, verbose=0, mode='auto')
<<<<<<< Updated upstream
<<<<<<< Updated upstream
model.fit(data, label, batch_size=200, epochs=10, verbose=1, callbacks=[es, lr_decay])
result = model.predict(test, batch_size=None, verbose=1)
prediction = pd.DataFrame({'malware': result[:,0]})
prediction.to_csv('prediction_rnn.csv', index=True,header=True)
