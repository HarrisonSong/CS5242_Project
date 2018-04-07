#import matplotlib.pyplot as plt
from keras.layers import Embedding, ELU, Dropout, Flatten, Input, Dense, BatchNormalization, Conv1D, MaxPooling1D, LSTM
from keras.layers import concatenate, multiply
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

data = pd.read_csv('sample_data.csv',header=None,dtype='float',names=list(range(4096)))
test = pd.read_csv('sample_data.csv',header=None,dtype='float',names=list(range(4096)))
label = pd.read_csv('sample_label.csv')['category'].values.reshape(-1, 1)

# print(data.head)
# print(label.shape)
# print(test.shape)


maxlen=4096
embed_size=128
lstm_layer_size = 100
num_layers = 1

main_input = Input(shape=(None,), name='main_input')
emb = Embedding(256, embed_size, input_length=maxlen, embeddings_regularizer=l2(1e-4))(main_input)
emb = Dropout(0.2)(emb)
# conv = Conv1D(filters=32, kernel_size=3, padding='same', activation='relu')(emb)
# emb = MaxPooling1D(pool_size=2)(conv)

hs = [] #hidden states from each LSTM layer stored here
lstm = LSTM(lstm_layer_size, dropout=0.2, recurrent_dropout=0.2, kernel_regularizer=l2(1e-5), recurrent_regularizer=l2(1e-5), return_sequences=True)(emb)
hs.append(lstm)
for l in range(1, num_layers):
    hs.append(LSTM(lstm_layer_size, dropout=0.2, recurrent_dropout=0.2, kernel_regularizer=l2(1e-5), recurrent_regularizer=l2(1e-5), return_sequences=True)(hs[-1]))
local_states = hs[0]
average_active = Lambda(function=lambda x: K.mean(x, axis=1), output_shape=lambda shape: (shape[0],) + shape[2:])(local_states) # this produces h
state_size = lstm_layer_size*num_layers

# Attention mechanism starts here
attn_cntx = concatenate([local_states, RepeatVector(maxlen)(average_active)])
attn_cntx = TimeDistributed(Dense(lstm_layer_size, activation='linear', kernel_regularizer=l2(1e-4)))(attn_cntx)
attn_cntx = TimeDistributed(BatchNormalization())(attn_cntx)
attn_cntx = TimeDistributed(Activation('tanh'))(attn_cntx)
attn_cntx = TimeDistributed(Dropout(0.5))(attn_cntx)

attn = TimeDistributed(Dense(1, activation='linear', kernel_regularizer=l2(1e-4)))(attn_cntx)
attn = Flatten()(attn)
attn = Activation('softmax')(attn)
attn = Reshape((maxlen, 1))(attn)
attn = Lambda(function=lambda x: x, output_shape=lambda shape: (shape[:2] + tuple([state_size])))(attn) # repeats value to make a specific shape

final_context = multiply([attn, local_states])
final_context = Lambda(function=lambda x: K.sum(x, axis=1), output_shape=lambda shape: (shape[0],) + shape[2:])(final_context) # eq(2), Ti=1 αihi
final_context = Dense(state_size, activation='linear', kernel_regularizer=l2(1e-4))(final_context)
final_context = BatchNormalization()(final_context)
final_context = Activation('tanh')(final_context)
final_context = Dropout(0.5)(final_context)

loss_out = Dense(1, activation='sigmoid', name='loss_out')(final_context)
model = Model(inputs=[main_input], outputs=[loss_out])

def scheduler(epoch):
    if epoch%1==0 and epoch!=0:
        lr = K.get_value(model.optimizer.lr)
        K.set_value(model.optimizer.lr, lr*.5)
        print("lr changed to {}".format(lr*.5))
    return K.get_value(model.optimizer.lr)

lr_decay = LearningRateScheduler(scheduler)

optimizer = Adam(lr=0.001, clipnorm=1.0)
model.compile(optimizer, loss='binary_crossentropy', metrics=['binary_accuracy'])

es = EarlyStopping(monitor='binary_accuracy', min_delta=0, patience=0, verbose=0, mode='auto')
model.fit(data, label, batch_size=200, epochs=4, verbose=1, callbacks=[es, lr_decay])
result = model.predict(test, batch_size=200, verbose=1)
prediction = pd.DataFrame({'malware': result[:,0]})
prediction.to_csv('prediction_rnn.csv', index=True,header=True)

