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
df_train = pd.read_csv("train.csv",header=None,delimiter=',',dtype='float64',names=list(range(4096))).fillna(0)
X_train = df_train.get_values()
df_label = pd.read_csv("train_label.csv",delimiter=',')
Y_train = df_label['category'].get_values()
Y_train = Y_train.reshape(-1,1)
print(X_train.shape)
maxlen = 4096
embed_size = 128
def scheduler(epoch):
    if epoch%1==0 and epoch!=0:
        lr = K.get_value(model.optimizer.lr)
        K.set_value(model.optimizer.lr, lr*.9)
        print("lr changed to {}".format(lr*.9))
    return K.get_value(model.optimizer.lr)

lr_decay = LearningRateScheduler(scheduler)

main_input = Input(shape=(maxlen,), dtype='float64',name='main_input')
emb = Embedding(256, embed_size, input_length=maxlen,embeddings_regularizer=regularizers.l2(1e-4))(main_input)
x = Flatten()(emb)

num_layers = 2
for i in range(num_layers):
    W_reg = regularizers.l2(1e-4)
    if i == 0:
        W_reg = regularizers.l2(1e-4)
    x = Dense(10, activation='linear',kernel_regularizer=regularizers.l2(1e-4))(x)
    x = BatchNormalization()(x)
    x = ELU()(x)
    #if i == num_layers-1:
        #x = DeCovRegularization(0.1)(x)
    x = Dropout(0.5)(x)

    loss_out = Dense(1, activation='sigmoid',name='loss_out')(x)
model = Model(input=[main_input], output=[loss_out])
optimizer = Adam(lr=0.001)#RMSprop(lr=0.01)
model.compile(optimizer, loss='binary_crossentropy',metrics=['mse', 'accuracy'])

model.fit(x=X_train, y=Y_train, batch_size=200, epochs=20, verbose=1, callbacks=[lr_decay], validation_split=0.0, validation_data=None, shuffle=True, class_weight=None, sample_weight=None, initial_epoch=0, steps_per_epoch=None, validation_steps=None)

x_test = pd.read_csv("test.csv",header=None,delimiter=',',dtype='float64',names=list(range(4096))).fillna(0)
X_test = df_train.get_values()
print(x_test.shape)

y=model.predict(x_test, batch_size=None, verbose=0, steps=None)
#y[y>=0.5]=1
#y=y.astype(int)
print(y.shape[0])

s=np.arange(y.shape[0]).astype(int)
a= np.zeros((y.shape[0],2))
a= np.vstack([s,y.reshape(-1)])
print(a.T)
np.savetxt("out.csv", a.T, delimiter=',', fmt='%i,%f', header="sample_id,malware", comments="")
print("finish")
