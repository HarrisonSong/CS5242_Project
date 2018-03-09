from keras.layers import Embedding, ELU, Dropout, Flatten, Input, Dense, BatchNormalization, SpatialDropout1D
from keras.regularizers import l2, l1_l2
from keras.optimizers import Adam, Nadam
from keras import Model
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from keras.utils import multi_gpu_model

data = pd.read_csv("train.csv",header=None,dtype='float64',names=list(range(4096))).fillna(0)
label = pd.read_csv('train_label.csv')['category'].values.reshape(-1, 1)
test = pd.read_csv('test.csv',header=None,dtype='float64',names=list(range(4096))).fillna(0)
print(data.shape)
print(label.shape)
print(test.shape)

maxlen=4096
embed_size=16
main_input = Input(shape=(maxlen,), dtype='float64', name='main_input')
emb = Embedding(256, embed_size, input_length=maxlen, embeddings_regularizer=l2(1e-4))(main_input)
#emb = Dropout(0.2)(emb)
x = Flatten()(emb)
num_layers = 4
for i in range(num_layers):
    W_reg = l2(1e-4)
    if i == 0:
        W_reg = l2(1e-4)
    x = Dense(100, activation='linear', kernel_regularizer=W_reg)(x)
    x = BatchNormalization()(x)
    x = ELU()(x)
#     if i == num_layers-1:
#         x = DeCovRegularization(0.1)(x)
    x = Dropout(0.5)(x)

loss_out = Dense(1, activation='sigmoid',  name='loss_out')(x)

# Replicates `model` on 8 GPUs.
# This assumes that your machine has 8 available GPUs.
#parallel_model = multi_gpu_model(model, gpus=8)
model = Model(inputs=[main_input], outputs=[loss_out])
optimizer = Adam(lr=0.001, decay=0.004)
#optimizer = Nadam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=None, schedule_decay=0.004)
model.compile(optimizer, loss='binary_crossentropy', metrics=['mse', 'binary_accuracy'])

model.fit(data, label, batch_size=20, epochs=5, verbose=1)
result = model.predict(test, batch_size=20, verbose=1)
output = []
for item in result:
    if item >= 0.5:
        output.append(1)
    else:
        output.append(0)
prediction = pd.DataFrame({'category': output})
prediction.to_csv('prediction.csv', index=True, header=True)
