import tensorflow as tf
import numpy as np
from tensorflow import keras
import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib as mpl
import csv

keras.backend.clear_session()
REDUCTION_FILTERS = {
    'Inception-v4' : {
        'k' : 192,
        'l' : 224,
        'm' : 256,
        'n' : 384
    },
    'Inception-ResNet-v2' : {
        'k' : 256,
        'l' : 256,
        'm' : 384,
        'n' : 384
    }
}
WEIGHTS_TYPE = 'Inception-v4'

def conv2d_bn(filters, kernel_size, padding='v', strides=1, activation='relu', **kwargs):
    padding = 'valid' if padding == 'v' else 'same'
    x, y = kernel_size.split('x')
    kernel_size = [int(x), int(y)]
    return keras.models.Sequential([
        keras.layers.Conv2D(filters=filters, kernel_size=kernel_size, strides=strides, padding=padding,**kwargs),
        keras.layers.BatchNormalization(scale=False),
        keras.layers.Activation(activation),
    ])

def conv2d(filters, kernel_size, padding='v', strides=1, activation='relu', **kwargs):
    padding = 'valid' if padding == 'v' else 'same'
    x, y = kernel_size.split('x')
    kernel_size = [int(x), int(y)]
    return keras.layers.Conv2D(filters=filters, kernel_size=kernel_size, strides=strides, padding=padding,activation=activation, **kwargs)


def max_pool2d(pool_size='2x2', padding='v', strides=1):
    x, y = pool_size.split('x')
    pool_size = [int(x), int(y)]
    padding = 'valid' if padding == 'v' else 'same'
    return keras.layers.MaxPool2D(pool_size=pool_size, strides=strides, padding=padding)

def avg_pool2d(pool_size='2x2', padding='v', strides=1):
    x, y = pool_size.split('x')
    pool_size = [int(x), int(y)]
    padding = 'valid' if padding == 'v' else 'same'
    return keras.layers.AveragePooling2D(pool_size=pool_size, strides=strides, padding=padding)


class Stem(keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #conv 32 3x3 2 v
        #conv 32 3x3 v
        #conv 64 3x3 s
        #max pool 3x3 v + conv 96 3x3 2 v
        #conv 64 1x1 s   / 
        #conv 64 7x1 s / 
        #conv 64 1x7 s / conv 64 1x1 s
        #conv 96 3x3 s + conv 96 3x3 s
        #conv 192 3x3 v / max pool 2 v
        
                                               #299x299x3
        self.conv1 = conv2d_bn(32, '3x3', 'v', 2) #149x149x3
        self.conv2 = conv2d_bn(32, '3x3', 'v', 1) #147x147x3
        self.conv3 = conv2d_bn(64, '3x3', 's', 1) #147x147x3

        self.max_pool4_1 = max_pool2d('3x3', 'v', 2) #1
        self.conv4_2 = conv2d_bn(32, '3x3', 'v', 2)
        
        self.concat5 = keras.layers.Concatenate(axis=-1)
        
        self.conv6_1 = conv2d_bn(64, '1x1', 's', 1)
        self.conv6_2 = conv2d_bn(64, '7x1', 's', 1)
        self.conv6_3 = conv2d_bn(96, '1x7', 's', 1)
        self.conv6_4 = conv2d_bn(96, '3x3', 'v', 1)

        self.conv7_1 = conv2d_bn(64, '1x1', 's', 1)
        self.conv7_2 = conv2d_bn(96, '3x3', 'v', 1)

        self.concat8 = keras.layers.Concatenate(axis=-1)

        self.conv9_1 = conv2d_bn(192, '3x3', 'v', 2)
        self.max_pool9_2 = max_pool2d('2x2', 'v', 2)

        self.concat10 = keras.layers.Concatenate(axis=-1)
    
    def call(self, inputs):
        Z = inputs
        Z = self.conv1(Z)
        Z = self.conv2(Z)
        Z = self.conv3(Z)
        Z_1 = self.max_pool4_1(Z)
        Z_2 = self.conv4_2(Z)
        Z = self.concat5([Z_1, Z_2])

        Z_1 = self.conv6_1(Z)
        Z_1 = self.conv6_2(Z_1)
        Z_1 = self.conv6_3(Z_1)
        Z_1 = self.conv6_4(Z_1)

        Z_2 = self.conv7_1(Z)
        Z_2 = self.conv7_2(Z_2)

        Z = self.concat8([Z_1, Z_2])
        
        Z_1 = self.conv9_1(Z)
        Z_2 = self.max_pool9_2(Z)

        return self.concat10([Z_1, Z_2])

        
class ReductionA(keras.layers.Layer):
    def __init__(self, filters, **kwargs):
        super().__init__(**kwargs)

        self.max_pool1 = max_pool2d('3x3', 'v', 2)

        self.conv2 = conv2d_bn(filters['n'], '3x3', 'v', 2)
        
        self.conv3_1 = conv2d_bn(filters['k'], '1x1', 's', 1)
        self.conv3_2 = conv2d_bn(filters['l'], '3x3', 's', 1)
        self.conv3_3 = conv2d_bn(filters['m'], '3x3', 'v', 2)

        self.concat = keras.layers.Concatenate(axis=-1)
    
    def call(self, inputs):
        
        Z = inputs

        Z_1 = self.max_pool1(Z)

        Z_2 = self.conv2(Z)

        Z_3 = self.conv3_1(Z)
        Z_3 = self.conv3_2(Z_3)
        Z_3 = self.conv3_3(Z_3)

        return self.concat([Z_1, Z_2, Z_3])


class InceptionA(keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.avg_pool_1_1 = avg_pool2d('2x2', 's', 1)
        self.conv1_2 = conv2d_bn(96, '1x1', 's', 1)
        
        self.conv2 = conv2d_bn(96, '1x1', 's', 1)
        
        self.conv3_1 = conv2d_bn(64, '1x1', 's', 1)
        self.conv3_2 = conv2d_bn(96, '3x3', 's', 1)

        self.conv4_1 = conv2d_bn(64, '1x1', 's', 1)
        self.conv4_2 = conv2d_bn(96, '3x3', 's', 1)
        self.conv4_3 = conv2d_bn(96, '3x3', 's', 1)

        self.concat = keras.layers.Concatenate(axis=-1)
    
    def call(self, inputs):

        Z = inputs

        Z_1 = self.avg_pool_1_1(Z)
        Z_1 = self.conv1_2(Z_1)

        Z_2 = self.conv2(Z)

        Z_3 = self.conv3_1(Z)
        Z_3 = self.conv3_2(Z_3)

        Z_4 = self.conv4_1(Z)
        Z_4 = self.conv4_2(Z_4)
        Z_4 = self.conv4_3(Z_4)
        
        return keras.layers.Concatenate(axis=-1)([Z_1, Z_2, Z_3, Z_4])

class InceptionB(keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.avg_pool_1_1 = avg_pool2d('2x2', 's', 1)
        self.conv1_2 = conv2d_bn(128, '1x1', 's', 1)

        self.conv2 = conv2d_bn(384, '1x1', 's', 1)

        self.conv3_1 = conv2d_bn(192, '1x1', 's', 1)
        self.conv3_2 = conv2d_bn(224, '7x1', 's', 1)
        self.conv3_3 = conv2d_bn(256, '1x7', 's', 1)
        
        self.conv4_1 = conv2d_bn(192, '1x1', 's', 1)
        self.conv4_2 = conv2d_bn(192, '1x7', 's', 1)
        self.conv4_3 = conv2d_bn(224, '7x1', 's', 1)
        self.conv4_4 = conv2d_bn(224, '1x7', 's', 1)
        self.conv4_5 = conv2d_bn(256, '7x1', 's', 1)

        self.concat = keras.layers.Concatenate(axis=-1)
    
    def call(self, inputs):

        Z = inputs

        Z_1 = self.avg_pool_1_1(Z)
        Z_1 = self.conv1_2(Z_1)

        Z_2 = self.conv2(Z)

        Z_3 = self.conv3_1(Z)
        Z_3 = self.conv3_2(Z_3)
        Z_3 = self.conv3_3(Z_3)

        Z_4 = self.conv4_1(Z)
        Z_4 = self.conv4_2(Z_4)
        Z_4 = self.conv4_3(Z_4)
        Z_4 = self.conv4_4(Z_4)
        Z_4 = self.conv4_5(Z_4)
    
        return self.concat([Z_1, Z_2, Z_3, Z_3])

class ReductionB(keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.max_pool1 = max_pool2d('3x3', 'v', 2)

        self.conv2_1 = conv2d_bn(192, '1x1', 's', 1)
        self.conv2_2 = conv2d_bn(192, '3x3', 'v', 2)

        self.conv3_1 = conv2d_bn(256, '1x1', 's', 1)
        self.conv3_2 = conv2d_bn(256, '1x7', 's', 1)
        self.conv3_3 = conv2d_bn(320, '7x1', 's', 1)
        self.conv3_4 = conv2d_bn(320, '3x3', 'v', 2)

        self.concat = keras.layers.Concatenate(axis=-1)
    
    def call(self, inputs):
        
        Z = inputs

        Z_1 = self.max_pool1(Z)

        Z_2 = self.conv2_1(Z)
        Z_2 = self.conv2_2(Z_2)

        Z_3 = self.conv3_1(Z)
        Z_3 = self.conv3_2(Z_3)
        Z_3 = self.conv3_3(Z_3)
        Z_3 = self.conv3_4(Z_3)

        return self.concat([Z_1, Z_2, Z_3])


class InceptionC(keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.arg_pool1_1 = avg_pool2d('2x2', 's', 1)
        self.conv1_2 = conv2d_bn(256, '1x1', 's', 1)

        self.conv2 = conv2d_bn(256, '1x1', 's', 1)
        
        self.conv3_1 = conv2d_bn(384, '1x1', 's', 1)
        self.conv3_2_1 = conv2d_bn(256, '1x3', 's', 1)
        self.conv3_2_2 = conv2d_bn(256, '3x1', 's', 1)

        self.conv4_1 = conv2d_bn(384, '1x1', 's', 1)
        self.conv4_2 = conv2d_bn(448, '1x3', 's', 1)
        self.conv4_3 = conv2d_bn(512, '3x1', 's', 1)
        self.conv4_4_1 = conv2d_bn(256, '3x1', 's', 1)
        self.conv4_4_2 = conv2d_bn(256, '1x3', 's', 1)

        self.concat = keras.layers.Concatenate(axis=-1)
    
    def call(self, inputs):
        Z = inputs

        Z_1 = self.arg_pool1_1(Z)
        Z_1 = self.conv1_2(Z_1)

        Z_2 = self.conv2(Z)

        Z_3 = self.conv3_1(Z)
        Z_3_1 = self.conv3_2_1(Z_3)
        Z_3_2 = self.conv3_2_2(Z_3)

        Z_4 = self.conv4_1(Z)
        Z_4 = self.conv4_2(Z_4)
        Z_4 = self.conv4_3(Z_4)
        Z_4_1 = self.conv4_4_1(Z_4)
        Z_4_2 = self.conv4_4_2(Z_4)

        return self.concat([Z_1, Z_2, Z_3_1, Z_3_2, Z_4_1, Z_4_2])