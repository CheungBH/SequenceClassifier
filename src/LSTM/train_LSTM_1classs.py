import os
import numpy as np
import keras.backend as K
from keras.models import Sequential
from keras.layers import Dense, Activation, LSTM, Masking, Dropout, BatchNormalization
import config

from keras.callbacks import LearningRateScheduler
from keras.callbacks import ModelCheckpoint, CSVLogger

from matplotlib import pyplot as plt
import warnings
warnings.filterwarnings('ignore')

input_channels = config.training_frame
seq_length = config.kps_num


class LSTMTrainer:
    def __init__(self, data_path, epoch, dropout, lr, model_name, log_name, batch_size):
        self.dropout = dropout
        self.epoch = epoch
        self.data_path = data_path
        self.lr = lr
        self.model_name = model_name
        self.log_name = log_name
        self.batch_size = batch_size
        self.model = self.__get_model()
        self.loss_graph_name = (self.model_name.replace("model", "LSTM_graph/loss")).replace(".h5", ".jpg")
        self.acc_graph_name = (self.model_name.replace("model", "LSTM_graph/acc")).replace(".h5", ".jpg")
        self.data = open(os.path.join(data_path, "data.txt"), "r")
        self.label = open(os.path.join(data_path, "label.txt"), "r")
        self.cls_path = os.path.join(data_path, "cls.txt")

    def __ls_preprocess(self, ls):
        try:
            ls.remove("\n")
        except:
            pass

        while True:
            try:
                ls.remove("")
            except ValueError:
                break
        return ls

    def __load_data(self):
        label = [int(line[:-1]) for line in self.label.readlines()]
        data = []
        for line in self.data.readlines():
            origin_ls = self.__ls_preprocess(line.split("\t"))
            ls = [float(item) for item in origin_ls]
            data.append(np.array(ls).reshape((input_channels, seq_length)))
        return np.array(data), np.array(label)

    def __get_model(self):
        model = Sequential()
        model.add(Masking(mask_value=-1, input_shape=(input_channels, seq_length)))  # 此函数定义是，如果后面是-1就不参与计算
        # model.add(LSTM(16,dropout=0.2,recurrent_dropout=0.2, return_sequences=True))
        model.add(LSTM(128, dropout=self.dropout, recurrent_dropout=self.dropout, return_sequences=True))
        model.add(LSTM(128, dropout=self.dropout, recurrent_dropout=self.dropout, return_sequences=False))
        model.add(Dense(64, activation='relu'))
        model.add(Dense(16, activation='relu'))
        model.add(Dense(1, activation='sigmoid'))
        return model

    def scheduler(self, epoch):
        if epoch % 10 == 0 and epoch != 0:
            lr = K.get_value(self.model.optimizer.lr)
            K.set_value(self.model.optimizer.lr, lr * 0.95)
        return K.get_value(self.model.optimizer.lr)

    def __plot_loss(self, hist):
        fig = plt.figure(figsize=(7.5, 5))
        plt.plot(hist['loss'], linewidth=2.0)
        plt.plot(hist['val_loss'], linewidth=2.0)
        plt.title('Model Loss', fontsize=15)
        plt.ylabel('loss', fontsize=15)
        plt.xlabel('epoch', fontsize=15)
        plt.legend(['train', 'val'], loc='upper right', fontsize=15)
        plt.xticks(fontsize=10)
        plt.yticks(fontsize=10)
        plt.tight_layout()
        plt.savefig(self.loss_graph_name)

    def __plot_acc(self, hist):
        fig = plt.figure(figsize=(7.5, 5))
        try:
            plt.plot(hist['accuracy'], linewidth=2.0)
            plt.plot(hist['val_accuracy'], linewidth=2.0)
        except:
            plt.plot(hist['acc'], linewidth=2.0)
            plt.plot(hist['val_acc'], linewidth=2.0)
        plt.title('Model Accuracy', fontsize=15)
        plt.ylabel('accuracy', fontsize=15)
        plt.xlabel('epoch', fontsize=15)
        plt.legend(['train', 'val'], loc='lower right', fontsize=15)
        plt.xticks(fontsize=10)
        plt.yticks(fontsize=10)
        plt.tight_layout()
        plt.savefig(self.acc_graph_name)

    def train_LSTM(self):
        reduce_lr = LearningRateScheduler(self.scheduler)
        filename = self.log_name
        csv_logger = CSVLogger(filename, separator=',', append=True)
        callbacks_list = [csv_logger, reduce_lr]
        self.model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
        train_x, train_y = self.__load_data()
        hist = self.model.fit(x=train_x, y=train_y, batch_size=self.batch_size, epochs=self.epoch, verbose=1,
                              callbacks=callbacks_list, validation_split=0.2)
        self.model.save(self.model_name)
        self.__plot_loss(hist.history)
        self.__plot_acc(hist.history)


if __name__ == '__main__':
    os.makedirs("LSTM_graph",exist_ok=True)
    LSTMTrainer("../../tmp/input1", 1000, 0.2, "", "LSTM.h5", 'train_log.csv', 32).train_LSTM()