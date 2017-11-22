# coding=utf-8
from keras.models import Input, Model
from keras.layers import Conv2D, Concatenate, MaxPooling2D, Conv2DTranspose
from keras.layers import UpSampling2D, Dropout, BatchNormalization
from keras.optimizers import Adam
from keras import backend as K
from keras.layers import Reshape
from keras.layers import Activation

'''
U-Net: Convolutional Networks for Biomedical Image Segmentation
(https://arxiv.org/abs/1505.04597)
---
img_shape: (height, width, channels)
out_ch: number of output channels
start_ch: number of channels of the first conv
depth: zero indexed depth of the U-structure
inc_rate: rate at which the conv channels will increase
activation: activation function after convolutions
dropout: amount of dropout in the contracting part
batchnorm: adds Batch Normalization if true
maxpool: use strided conv instead of maxpooling if false
upconv: use transposed conv instead of upsamping + conv if false
residual: add residual connections around each conv block if true
'''


def conv_block(m, dim, acti, bn, res, do=0):
    n = Conv2D(dim, 3, activation=acti, padding='same')(m)
    n = BatchNormalization()(n) if bn else n
    n = Dropout(do)(n) if do else n
    n = Conv2D(dim, 3, activation=acti, padding='same')(n)
    n = BatchNormalization()(n) if bn else n
    return Concatenate()([m, n]) if res else n


def level_block(m, dim, depth, inc, acti, do, bn, mp, up, res):
    if depth > 0:
        n = conv_block(m, dim, acti, bn, res)
        m = MaxPooling2D()(n) if mp else Conv2D(dim, 3, strides=2, padding='same')(n)
        m = level_block(m, int(inc*dim), depth-1, inc, acti, do, bn, mp, up, res)
        if up:
            m = UpSampling2D()(m)
            m = Conv2D(dim, 2, activation=acti, padding='same')(m)
        else:
            m = Conv2DTranspose(dim, 3, strides=2, activation=acti, padding='same')(m)
        n = Concatenate()([n, m])
        m = conv_block(n, dim, acti, bn, res)
    else:
        m = conv_block(m, dim, acti, bn, res, do)
    return m


def build(h, w, nc, loss='categorical_crossentropy',
          # optimizer='adadelta'):
          optimizer=None,
          metrics=None,
          start_ch=64, depth=4, inc_rate=2., activation='relu',
          dropout=0.5, batchnorm=False, maxpool=True, upconv=True,
          residual=False, **kwargs):
    i = Input(shape=(h, w, 3), name='image')
    conv_out = level_block(i, start_ch, depth, inc_rate, activation,
                           dropout, batchnorm, maxpool, upconv, residual)
    conv_out = Conv2D(nc, 1, activation='softmax')(conv_out)

    hw = K.int_shape(conv_out)[1] * K.int_shape(conv_out)[2]
    target_shape = (hw, nc)
    decoder = Reshape(target_shape=target_shape)(conv_out)

    decoder = Activation('softmax', name='output')(decoder)

    model = Model(inputs=i, outputs=decoder)
    name = 'unet2'

    if optimizer is None:
        optimizer = Adam(lr=1e-4)
    if metrics is None:
        metrics = ['accuracy']
    model.compile(optimizer=optimizer, loss=loss,
                  metrics=metrics)

    return model, name


def transfer_weights(model, **kwargs):
    return model
