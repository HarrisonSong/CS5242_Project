#import matplotlib.pyplot as plt
from keras.layers import Embedding, ELU, Dropout, Flatten, Input, Dense, BatchNormalization, SpatialDropout1D, CuDNNLSTM
from keras.layers import concatenate, multiply
from keras.layers import TimeDistributed, Reshape, RepeatVector, Lambda, Activation
from keras.regularizers import l2, l1_l2
from keras.optimizers import Adam, Nadam
from keras.callbacks import EarlyStopping
from keras import Model
from keras.utils.np_utils import to_categorical
import pandas as pd
import numpy as np
from keras import backend as K

data = pd.read_csv('train.csv',header=None,dtype='float',names=list(range(4096))).fillna(0)
test = pd.read_csv('test.csv',header=None,dtype='float',names=list(range(4096))).fillna(0)
label = pd.read_csv('train_label.csv')['category'].values.reshape(-1, 1)

maxlen=4096
embed_size=16
lstm_layer_size = 10
num_layers = 3

main_input = Input(shape=(maxlen,), name='main_input')
emb = Embedding(256, embed_size, input_length=maxlen, embeddings_regularizer=l2(1e-4))(main_input)
# drop = SpatialDropout1D(0.2)(emb)
hs = [] #hidden states from each LSTM layer stored here
lstm = CuDNNLSTM(lstm_layer_size,  kernel_regularizer=l2(1e-5), recurrent_regularizer=l2(1e-5), return_sequences=True)(emb)
hs.append(lstm)
for l in range(1, num_layers):
    hs.append(CuDNNLSTM(lstm_layer_size, kernel_regularizer=l2(1e-5), recurrent_regularizer=l2(1e-5), return_sequences=True)(hs[-1]))
local_states = concatenate(hs)
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
optimizer = Adam(lr=0.001, clipnorm=1.0, decay=0.004)
model.compile(optimizer, loss='binary_crossentropy', metrics=['binary_accuracy'])

es = EarlyStopping(monitor='binary_accuracy', min_delta=0, patience=0, verbose=0, mode='auto')
model.fit(data, label, batch_size=20, epochs=2, verbose=1, callbacks=[es])
result = model.predict(test, batch_size=20, verbose=1)

output = []
for item in result:
    if item >= 0.5:
        output.append(1)
    else:
        output.append(0)
prediction = pd.DataFrame({'category': output})
prediction.to_csv('prediction_rnn.csv', index=True,header=True)
