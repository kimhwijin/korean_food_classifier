from tkinter import W
from matplotlib.backend_bases import MouseEvent
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
    'Inception-V4' : {
        'A' : {
            'k' : 192,
            'l' : 224,
            'm' : 256,
            'n' : 384
        },
        'B' : {
            'conv2_1': 192,
            'conv2_2': 192,
            'conv3_1': 256,
            'conv3_2': 256,
            'conv3_3': 320,
            'conv3_4': 320
        }
    },
    'Inception-ResNet-V2' : {
        'A' : {
            'k' : 192,
            'l' : 224,
            'm' : 256,
            'n' : 384
        },
        'B' : {
            'conv2_1': 256,
            'conv2_2': 384,
            'conv3_1': 256,
            'conv3_2': 288,
            'conv4_1': 256,
            'conv4_2': 288,
            'conv4_3': 320
        }
    }
}
STEM_FILTERS = {
    'conv1': 32, 
    'conv2': 32, 
    'conv3': 64,
    'conv4_2': 32,
    'conv6_1': 64, 
    'conv6_2': 64,
    'conv6_3': 96,
    'conv6_4': 96, 
    'conv7_1': 64,
    'conv7_2': 96,
    'conv9_1': 192
    }

INCEPTION_FILTERS = {
    'Inception-V4' : {
        'A' : {
            'conv1_2': 96,
            'conv2': 96,
            'conv3_1': 64,
            'conv3_2': 96,
            'conv4_1': 96,
            'conv4_2': 96,
            'conv4_3': 96
        },
        'B' : {
            'conv1_2': 128,
            'conv2': 384,
            'conv3_1': 192,
            'conv3_2': 224,
            'conv3_3': 256,
            'conv4_1': 192,
            'conv4_2': 192,
            'conv4_3': 224,
            'conv4_4': 224,
            'conv4_5': 256
        },
        'C' : {
            'conv1_2': 256,
            'conv2': 256,
            'conv3_1': 384,
            'conv3_2_1': 256,
            'conv3_2_2': 256,
            'conv4_1': 384,
            'conv4_2': 448,
            'conv4_3': 512,
            'conv4_4_1': 256,
            'conv4_4_2': 256
        }
    },
    'Inception-ResNet-V2': {
        'A' : {
            'conv1': 32,
            'conv2_1': 32,
            'conv2_2': 32,
            'conv3_1': 32,
            'conv3_2': 48,
            'conv3_3': 64,
            'conv4': 384
        },
        'B' : {
            'conv1' : 192,
            'conv2_1' : 128,
            'conv2_2' : 160,
            'conv2_3' : 192,
            'conv4' : 1154
        },
        'C' : {
            'conv1' : 192,
            'conv2_1' : 192,
            'conv2_2' : 224,
            'conv2_3' : 256,
            'conv4' : 2048
        }

    }
}


WEIGHTS_TYPE = 'Inception-V4'

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
    def __init__(self, filters=STEM_FILTERS, **kwargs):
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
        self.conv1 = conv2d_bn(filters['conv1'], '3x3', 'v', 2) #149x149x3
        self.conv2 = conv2d_bn(filters['conv2'], '3x3', 'v', 1) #147x147x3
        self.conv3 = conv2d_bn(filters['conv3'], '3x3', 's', 1) #147x147x3

        self.max_pool4_1 = max_pool2d('3x3', 'v', 2) #1
        self.conv4_2 = conv2d_bn(filters['conv4_2'], '3x3', 'v', 2)
        
        self.concat5 = keras.layers.Concatenate(axis=-1)
        
        self.conv6_1 = conv2d_bn(filters['conv6_1'], '1x1', 's', 1)
        self.conv6_2 = conv2d_bn(filters['conv6_2'], '7x1', 's', 1)
        self.conv6_3 = conv2d_bn(filters['conv6_3'], '1x7', 's', 1)
        self.conv6_4 = conv2d_bn(filters['conv6_4'], '3x3', 'v', 1)

        self.conv7_1 = conv2d_bn(filters['conv7_1'], '1x1', 's', 1)
        self.conv7_2 = conv2d_bn(filters['conv7_2'], '3x3', 'v', 1)

        self.concat8 = keras.layers.Concatenate(axis=-1)

        self.conv9_1 = conv2d_bn(filters['conv9_1'], '3x3', 'v', 2)
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
    def __init__(self, filters, **kwargs):
        super().__init__(**kwargs)
        
        self.avg_pool_1_1 = avg_pool2d('2x2', 's', 1)
        self.conv1_2 = conv2d_bn(filters['conv1_2'], '1x1', 's', 1)
        
        self.conv2 = conv2d_bn(filters['conv2'], '1x1', 's', 1)
        
        self.conv3_1 = conv2d_bn(filters['conv3_1'], '1x1', 's', 1)
        self.conv3_2 = conv2d_bn(filters['conv3_2'], '3x3', 's', 1)

        self.conv4_1 = conv2d_bn(filters['conv4_1'], '1x1', 's', 1)
        self.conv4_2 = conv2d_bn(filters['conv4_2'], '3x3', 's', 1)
        self.conv4_3 = conv2d_bn(filters['conv4_3'], '3x3', 's', 1)

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
    def __init__(self, filters,  **kwargs):
        super().__init__(**kwargs)

        self.avg_pool_1_1 = avg_pool2d('2x2', 's', 1)
        self.conv1_2 = conv2d_bn(filters['conv1_2'], '1x1', 's', 1)

        self.conv2 = conv2d_bn(filters['conv2'], '1x1', 's', 1)

        self.conv3_1 = conv2d_bn(filters['conv3_1'], '1x1', 's', 1)
        self.conv3_2 = conv2d_bn(filters['conv3_2'], '7x1', 's', 1)
        self.conv3_3 = conv2d_bn(filters['conv3_3'], '1x7', 's', 1)
        
        self.conv4_1 = conv2d_bn(filters['conv4_1'], '1x1', 's', 1)
        self.conv4_2 = conv2d_bn(filters['conv4_2'], '1x7', 's', 1)
        self.conv4_3 = conv2d_bn(filters['conv4_3'], '7x1', 's', 1)
        self.conv4_4 = conv2d_bn(filters['conv4_4'], '1x7', 's', 1)
        self.conv4_5 = conv2d_bn(filters['conv4_5'], '7x1', 's', 1)

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
    def __init__(self, filters, **kwargs):
        super().__init__(**kwargs)

        self.max_pool1 = max_pool2d('3x3', 'v', 2)

        self.conv2_1 = conv2d_bn(filters['conv2_1'], '1x1', 's', 1)
        self.conv2_2 = conv2d_bn(filters['conv2_2'], '3x3', 'v', 2)

        self.conv3_1 = conv2d_bn(filters['conv3_1'], '1x1', 's', 1)
        self.conv3_2 = conv2d_bn(filters['conv3_2'], '1x7', 's', 1)
        self.conv3_3 = conv2d_bn(filters['conv3_3'], '7x1', 's', 1)
        self.conv3_4 = conv2d_bn(filters['conv3_4'], '3x3', 'v', 2)

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
    def __init__(self, filters, **kwargs):
        super().__init__(**kwargs)

        self.arg_pool1_1 = avg_pool2d('2x2', 's', 1)
        self.conv1_2 = conv2d_bn(filters['conv1_2'], '1x1', 's', 1)

        self.conv2 = conv2d_bn(filters['conv2'], '1x1', 's', 1)
        
        self.conv3_1 = conv2d_bn(filters['conv3_1'], '1x1', 's', 1)
        self.conv3_2_1 = conv2d_bn(filters['conv3_2'], '1x3', 's', 1)
        self.conv3_2_2 = conv2d_bn(filters['conv3_3'], '3x1', 's', 1)

        self.conv4_1 = conv2d_bn(filters['conv4_1'], '1x1', 's', 1)
        self.conv4_2 = conv2d_bn(filters['conv4_2'], '1x3', 's', 1)
        self.conv4_3 = conv2d_bn(filters['conv4_3'], '3x1', 's', 1)
        self.conv4_4_1 = conv2d_bn(filters['conv4_4_1'], '3x1', 's', 1)
        self.conv4_4_2 = conv2d_bn(filters['conv4_4_2'], '1x3', 's', 1)

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



class InceptionModule(keras.layers.Layer):
    def __init__(self, filters, **kwargs):
        super().__init__(**kwargs)
        filters_1x1 = filters[0:2] + filters[3:4] + filters[5:]
        filters_3x3 = filters[2]
        filters_5x5 = filters[4]
        self.conv1x1_1 = keras.layers.Conv2D(filters_1x1[0], kernel_size=1, strides=1, padding="same")
        self.conv1x1_2 = keras.layers.Conv2D(filters_1x1[1], kernel_size=1, strides=1, padding="same")
        self.conv1x1_3 = keras.layers.Conv2D(filters_1x1[2], kernel_size=1, strides=1, padding="same")
        self.conv1x1_4 = keras.layers.Conv2D(filters_1x1[3], kernel_size=1, strides=1, padding="same")

        self.conv3 = keras.layers.Conv2D(filters_3x3, kernel_size=3, strides=1, padding="same")
        self.conv5 = keras.layers.Conv2D(filters_5x5, kernel_size=3, strides=1, padding="same")

        self.max_pool = keras.layers.MaxPooling2D(pool_size=3, strides=1, padding="same")

    def call(self, inputs):
        Z_1 = self.conv1x1_1(inputs)

        Z_2 = self.conv1x1_2(inputs)
        Z_2 = self.conv3(Z_2)

        Z_3 = self.conv1x1_3(inputs)
        Z_3 = self.conv5(Z_3)

        Z_4 = self.max_pool(inputs)
        Z_4 = self.conv1x1_4(Z_4)

        return keras.layers.Concatenate(axis=-1)([Z_1, Z_2, Z_3, Z_4])

class ResNetUnit(keras.layers.Layer):
    def __init__(self, filters, strides=1, activation='relu', **kwargs):
        super().__init__(**kwargs)
        self.activation = keras.activations.get(activation)
        self.main_layers = [
            keras.layers.Conv2D(filters, 3, strides=strides, padding="same", use_bias=False),
            keras.layers.BatchNormalization(),
            self.activation,
            keras.layers.Conv2D(filters, 3, strides=1, padding="same", use_bias=False),
            keras.layers.BatchNormalization()
        ]
        self.skip_layers = []
        if strides > 1:
            self.skip_layers = [
                keras.layers.Conv2D(filters, kernel_size=1, strides=strides, padding="same", use_bias=False),
                keras.layers.BatchNormalization()
            ]


    def call(self, inputs):
        Z = inputs
        for layer in self.main_layers:
            Z = layer(Z)
        skip_Z = inputs
        for layer in self.skip_layers:
            skip_Z = layer(skip_Z)
        
        return self.activation(skip_Z + Z)


class SE_Block(keras.layers.Layer):
    def __init__(self, filters, ratio=16, **kwargs):
        super().__init__(**kwargs)
        self.global_avg_pool = keras.layers.GlobalAveragePooling2D()
        self.squeeze = keras.layers.Dense(filters//ratio, activation='relu')
        self.excitation = keras.layers.Dense(filters, activation='sigmoid')

    def call(self, inputs):
        Z = self.global_avg_pool(inputs)
        Z = self.squeeze(Z)
        return self.excitation(Z)


class XceptionModule(keras.layers.Layer):
    def __init__(self, filter, **kwargs):
        super().__init__(**kwargs)
        self.depthwise = keras.layers.Conv2D(filter, kernel_size=3, strides=1, padding='same')
        self.pointwise = keras.layers.Conv2D(filter, kernel_size=1, strides=1, padding="same")
    
    def call(self, inputs):
        Z = inputs
        Z = self.depthwise(Z)
        Z = keras.layers.BatchNormalization()(Z)
        Z = self.pointwise(Z)
        return keras.layers.BatchNormalization()(Z)


class InceptionResNetA(keras.layers.Layer):
    def __init__(self, filters ,**kwargs):
        super().__init__(**kwargs)
        self.conv1 = conv2d_bn(filters['conv1'], '1x1', 's', 1)

        self.conv2_1 = conv2d_bn(filters['conv2_1'], '1x1', 's', 1)
        self.conv2_2 = conv2d_bn(filters['conv2_2'], '3x3', 's', 1)
        
        self.conv3_1 = conv2d_bn(filters['conv3_1'], '1x1', 's', 1)
        self.conv3_2 = conv2d_bn(filters['conv3_2'], '3x3', 's', 1)
        self.conv3_3 = conv2d_bn(filters['conv3_3'], '3x3', 's', 1)

        self.conv4 = keras.layers.Conv2D(filters['conv4'], kernel_size=1, strides=1, padding='same')
        
        self.concat = keras.layers.Concatenate(axis=-1)

        self.skip = keras.layers.Conv2D(filters['conv4'], kernel_size=1, strides=1, padding='same')
        
        self.bn = keras.layers.BatchNormalization()
        self.act = keras.layers.Activation('relu')

    def call(self, inputs):
        Z = inputs
        
        Z_1 = self.conv1(Z)
        
        Z_2 = self.conv2_1(Z)
        Z_2 = self.conv2_2(Z_2)

        Z_3 = self.conv3_1(Z)
        Z_3 = self.conv3_2(Z_3)
        Z_3 = self.conv3_3(Z_3)

        Z_4 = self.concat([Z_1, Z_2, Z_3])
        
        Z_4 = self.conv4(Z_4)

        Z_skip = self.skip(Z)

        Z = self.bn(Z_4 + Z_skip)
        Z = self.act(Z)

        return Z

class InceptionResNetB(keras.layers.Layer):
    def __init__(self, filters, **kwargs):
        super().__init__(**kwargs)
        self.conv1 = conv2d_bn(filters['conv1'], '1x1', 's', 1)

        self.conv2_1 = conv2d_bn(filters['conv2_1'], '1x1', 's', 1)
        self.conv2_2 = conv2d_bn(filters['conv2_2'], '1x7', 's', 1)
        self.conv2_3 = conv2d_bn(filters['conv2_3'], '7x1', 's', 1)

        self.conv4 = keras.layers.Conv2D(filters['conv4'], kernel_size=1, strides=1, padding='same')
        
        self.concat = keras.layers.Concatenate(axis=-1)

        self.skip = keras.layers.Conv2D(filters['conv4'], kernel_size=1, strides=1, padding='same')
        
        self.bn = keras.layers.BatchNormalization()
        self.act = keras.layers.Activation('relu')

    def call(self, inputs):
        Z = inputs
        
        Z_1 = self.conv1(Z)
        
        Z_2 = self.conv2_1(Z)
        Z_2 = self.conv2_2(Z_2)
        Z_2 = self.conv2_3(Z_2)

        Z_3 = self.concat([Z_1, Z_2])
        
        Z_3 = self.conv4(Z_3)

        Z_skip = self.skip(Z)

        Z = self.bn(Z_3 + Z_skip)
        Z = self.act(Z)

        return Z

class InceptionResNetC(keras.layers.Layer):
    def __init__(self, filters, **kwargs):
        super().__init__(**kwargs)

        self.conv1 = conv2d_bn(filters['conv1'], '1x1', 's', 1)

        self.conv2_1 = conv2d_bn(filters['conv2_1'], '1x1', 's', 1)
        self.conv2_2 = conv2d_bn(filters['conv2_2'], '1x7', 's', 1)
        self.conv2_3 = conv2d_bn(filters['conv2_3'], '7x1', 's', 1)

        self.conv4 = keras.layers.Conv2D(filters['conv4'], kernel_size=1, strides=1, padding='same')
        
        self.concat = keras.layers.Concatenate(axis=-1)

        self.skip = keras.layers.Conv2D(filters['conv4'], kernel_size=1, strides=1, padding='same')
        
        self.bn = keras.layers.BatchNormalization()
        self.act = keras.layers.Activation('relu')

    def call(self, inputs):
        Z = inputs
        
        Z_1 = self.conv1(Z)
        
        Z_2 = self.conv2_1(Z)
        Z_2 = self.conv2_2(Z_2)
        Z_2 = self.conv2_3(Z_2)

        Z_3 = self.concat([Z_1, Z_2])
        
        Z_3 = self.conv4(Z_3)

        Z_skip = self.skip(Z)

        Z = self.bn(Z_3 + Z_skip)
        Z = self.act(Z)

        return Z

class ReductionResNetB(keras.layers.Layer):
    def __init__(self, filters, **kwargs):
        super().__init__(**kwargs)

        self.max_pool1 = max_pool2d('3x3', 'v', 2)

        self.conv2_1 = conv2d_bn(filters['conv2_1'], '1x1', 's', 1)
        self.conv2_2 = conv2d_bn(filters['conv2_2'], '3x3', 'v', 2)

        self.conv3_1 = conv2d_bn(filters['conv3_1'], '1x1', 's', 1)
        self.conv3_2 = conv2d_bn(filters['conv3_2'], '3x3', 'v', 2)

        self.conv4_1 = conv2d_bn(filters['conv4_1'], '1x1', 's', 1)
        self.conv4_2 = conv2d_bn(filters['conv4_2'], '3x3', 's', 1)
        self.conv4_3 = conv2d_bn(filters['conv4_3'], '3x3', 'v', 2)

        self.concat = keras.layers.Concatenate(axis=-1)
    
    def call(self, inputs):
        
        Z = inputs

        Z_1 = self.max_pool1(Z)

        Z_2 = self.conv2_1(Z)
        Z_2 = self.conv2_2(Z_2)

        Z_3 = self.conv3_1(Z)
        Z_3 = self.conv3_2(Z_3)

        Z_4 = self.conv4_1(Z)
        Z_4 = self.conv4_2(Z_4)
        Z_4 = self.conv4_3(Z_4)

        return self.concat([Z_1, Z_2, Z_3, Z_4])



def make_InceptionV4(input_shape=[299, 299, 3], output_dim=150):
    
    WEIGHTS_TYPE = 'Inception-V4'

    inputs = keras.layers.Input(shape=input_shape)
    stem_module = Stem(STEM_FILTERS)
    Z = stem_module(inputs)

    #4 x inception A
    inceptionA_modules = []
    for _ in range(4):
        inceptionA_modules.append(InceptionA(INCEPTION_FILTERS[WEIGHTS_TYPE]['A']))
    for inceptionA_module in inceptionA_modules:
        Z = inceptionA_module(Z)

    reductionA = ReductionA(REDUCTION_FILTERS[WEIGHTS_TYPE]['A'])
    Z = reductionA(Z)

    #7 x inceptioin B
    inceptionB_modules = []
    for _ in range(7):
        inceptionB_modules.append(InceptionB(INCEPTION_FILTERS[WEIGHTS_TYPE]['A']))
    for inceptionB_module in inceptionB_modules:
        Z = inceptionB_module(Z)

    reductionB = ReductionB(REDUCTION_FILTERS[WEIGHTS_TYPE]['B'])
    Z = reductionB(Z)

    #3 x inception C
    inceptionC_modules = []
    for _ in range(3):
        inceptionC_modules.append(InceptionC(INCEPTION_FILTERS[WEIGHTS_TYPE]['C']))
    for inceptionC_module in inceptionC_modules:
        Z = inceptionC_module(Z)

    Z = keras.layers.GlobalAveragePooling2D()(Z)
    Z = keras.layers.Dropout(0.8)(Z)
    outputs = keras.layers.Dense(output_dim, activation='softmax')(Z)

    model = keras.models.Model(inputs=inputs, outputs=outputs)

    return model    


def make_InceptionResNetV2(input_shape=[299, 299, 3], output_dim=150):
    
    WEIGHTS_TYPE = 'Inception-ResNet-V2'

    inputs = keras.layers.Input(shape=input_shape)
    stem_module = Stem(STEM_FILTERS)
    Z = stem_module(inputs)

    #4 x inception A
    inceptionA_modules = []
    for _ in range(5):
        inceptionA_modules.append(InceptionResNetA(INCEPTION_FILTERS[WEIGHTS_TYPE]['A']))
    for inceptionA_module in inceptionA_modules:
        Z = inceptionA_module(Z)

    reductionA = ReductionA(REDUCTION_FILTERS[WEIGHTS_TYPE]['A'])
    Z = reductionA(Z)

    #7 x inceptioin B
    inceptionB_modules = []
    for _ in range(10):
        inceptionB_modules.append(InceptionResNetB(INCEPTION_FILTERS[WEIGHTS_TYPE]['B']))
    for inceptionB_module in inceptionB_modules:
        Z = inceptionB_module(Z)

    reductionB = ReductionResNetB(REDUCTION_FILTERS[WEIGHTS_TYPE]['B'])
    Z = reductionB(Z)

    #3 x inception C
    inceptionC_modules = []
    for _ in range(5):
        inceptionC_modules.append(InceptionResNetC(INCEPTION_FILTERS[WEIGHTS_TYPE]['C']))
    for inceptionC_module in inceptionC_modules:
        Z = inceptionC_module(Z)

    Z = keras.layers.GlobalAveragePooling2D()(Z)
    Z = keras.layers.Dropout(0.8)(Z)
    outputs = keras.layers.Dense(output_dim, activation='softmax')(Z)

    model = keras.models.Model(inputs=inputs, outputs=outputs)
    
    return model    
