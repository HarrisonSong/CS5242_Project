from keras.layers import Embedding, ELU, Dropout, Flatten, Input, Dense, BatchNormalization, Conv1D, MaxPooling1D, LSTM
from keras.layers import concatenate, multiply, Bidirectional
from keras.layers import TimeDistributed, Reshape, RepeatVector, Lambda, Activation
from keras.regularizers import l2, l1_l2
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping
from keras.utils.np_utils import to_categorical
from keras import backend as K
from keras import Model
from keras.callbacks import LearningRateScheduler

import numpy as np
import pandas as pd

data = pd.read_csv('train.csv',header=None,dtype='float',names=list(range(4096)))
test = pd.read_csv('test.csv',header=None,dtype='float',names=list(range(4096)))
label = pd.read_csv('train_label.csv')['category'].values.reshape(-1, 1)

# print(data.head)
# print(label.shape)
# print(test.shape)


maxlen=4096
embed_size=16
lstm_layer_size = 50
num_layers = 1

main_input = Input(shape=(None,), name='main_input')
emb = Embedding(256, embed_size, input_length=maxlen, embeddings_regularizer=l2(1e-4))(main_input)
emb = Dropout(0.5)(emb)

hs = [] #hidden states from each LSTM layer stored here
lstm = Bidirectional(LSTM(lstm_layer_size, dropout=0.5, recurrent_dropout=0.5, kernel_regularizer=l2(1e-5), recurrent_regularizer=l2(1e-5), return_sequences=True))(emb)
hs.append(lstm)
for l in range(1, num_layers):
    hs.append(LSTM(lstm_layer_size, dropout=0.5, recurrent_dropout=0.5, kernel_regularizer=l2(1e-5), recurrent_regularizer=l2(1e-5), return_sequences=True)(hs[-1]))
local_states = hs[0]
average_active = Lambda(function=lambda x: K.mean(x, axis=1), output_shape=lambda shape: (shape[0],) + shape[2:])(local_states) # this produces h
state_size = lstm_layer_size*num_layers*2

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
model.fit(data, label, batch_size=200, epochs=5, verbose=1, callbacks=[es, lr_decay])
result = model.predict(test, batch_size=200, verbose=1)
prediction = pd.DataFrame({'malware': result[:,0]})
prediction.to_csv('prediction_rnn.csv', index=True,header=True)
