from keras.layers import Embedding, ELU, Dropout, Flatten, Input, Dense, BatchNormalization, SpatialDropout1D
from keras.regularizers import l2, l1_l2
from keras.optimizers import Adam
from keras import Model
import matplotlib.pyplot as plt
import pandas as pd

maxlen=4096
embed_size=16
main_input = Input(shape=(maxlen,), dtype='int32',  name='main_input')
emb = Embedding(256, embed_size, input_length=maxlen, embeddings_regularizer=l2(1e-4))(main_input)
drop = SpatialDropout1D(0.2)(emb)
x = Flatten()(drop)
num_layers = 4
for i in range(num_layers):
    W_reg = l2(1e-4)
    if i == 0:
        W_reg = l1_l2(1e-4)
    x = Dense(maxlen, activation='linear', kernel_regularizer=W_reg)(x) 
    x = BatchNormalization()(x) 
    x = ELU()(x)
#     if i == num_layers-1:
#         x = DeCovRegularization(0.1)(x)
    x = Dropout(0.5)(x)
    
loss_out = Dense(1, activation='sigmoid',  name='loss_out')(x)
model = Model(inputs=[main_input], outputs=[loss_out])
optimizer = Adam(lr=0.001)
model.compile(optimizer, loss='binary_crossentropy')

data = pd.read_csv('sample_data.csv')
label = pd.read_csv('sample_label.csv')

model.fit(data, label['category'][1:], epochs=1, verbose=1)
