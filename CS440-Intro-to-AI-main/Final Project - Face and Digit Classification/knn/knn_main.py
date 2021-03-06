from typing import List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import datetime
import os
from knn import KNN


def load_labels_file(filename: str) -> List[int]:
    lines = read_lines(filename)
    labels = list()
    for line in lines:
        if line == '':
            break
        labels.append(int(line))
    return labels


def load_data_file(filename: str, width: int, height: int) -> np.array:
    lines = read_lines(filename)
    lines.reverse()
    items = list()
    while len(lines) > 0:
        data = list()
        for j in range(height):
            if len(lines) == 0:
                return np.array(items)
            line = lines.pop()
            data.extend(translate_pixels(line))
        data = np.array(data, dtype=int)
        items.append(data)
    return np.array(items)


def read_lines(filename: str):
    if os.path.exists(filename):
        return [l[:-1] for l in open(filename).readlines()]
    else:
        raise ValueError('Invalid data filename')


def translate_pixels(line: str) -> List[int]:
    new_line = list()
    for c in line:
        if c == '+':
            new_line.append(1)
        elif c == '#':
            new_line.append(2)
        else:
            new_line.append(0)
    return new_line


def main(raw_args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('dataset', help='choose dataset (face, digits)', type=str)
    parser.add_argument('-p', '--percent', help='choose percent of training data to use (ex: 15.5)', type=float, default=100.0)
    parser.add_argument('-k', '--kvals', help='k-vals to test, separated by commas (ex: \'35,20,15,1\'), leave blank to use optimal k (digits: 1, faces: 5)', type=str, default='')
    parser.add_argument('-f', '--file', help='append results to results file', action='store_true', default=False)
    parser.add_argument('-s', '--samples', help='use a random subset of 4 samples', action='store_true', default=False)
    parser.add_argument('-v', '--verbose', help='print verbose print strings', action='store_true', default=False)

    args = parser.parse_args(raw_args)
    dset = args.dataset
    training_percent = args.percent
    k_vals_in = args.kvals

    # parse kvals into dict
    if k_vals_in == '':
        if dset == 'digits':
            k_vals_in = [1]
        else:
            k_vals_in = [5]
    else:
        k_vals_in = [int(i) for i in k_vals_in.split(',')]
        k_vals_in.sort(reverse=True)
    k_vals = dict.fromkeys(k_vals_in, 0)

    if args.file:
        filename = 'knn_test_results_' + dset
        file = open(filename, 'a')

    if args.verbose:
        print('Getting data...')
    if dset == 'digits':
        width = 28
        height = 28
        training_data = load_data_file('../data/digitdata/trainingimages', width, height)
        training_labels = load_labels_file('../data/digitdata/traininglabels')
        test_data = load_data_file('../data/digitdata/testimages', width, height)
        test_labels = load_labels_file('../data/digitdata/testlabels')
    else:
        width = 60
        height = 70
        training_data = load_data_file('../data/facedata/facedatatrain', width, height)
        training_labels = load_labels_file('../data/facedata/facedatatrainlabels')
        test_data = load_data_file('../data/facedata/facedatatest', width, height)
        test_labels = load_labels_file('../data/facedata/facedatatestlabels')

    df_train = pd.DataFrame(data=training_data)
    df_train.insert(loc=df_train.shape[1], column='label', value=training_labels)
    df_test = pd.DataFrame(data=test_data)
    df_test.insert(loc=df_test.shape[1], column='label', value=test_labels)
    if training_percent == 100:
        df_train_sample = df_train
    else:
        df_train_sample = df_train.sample(frac=training_percent / 100)
    if args.samples:
        df_test_sample = df_test.sample(n=4)
    else:
        df_test_sample = df_test

    if args.verbose:
        print('Training KNN model...')
    my_knn = KNN(df_train_sample, dset=dset)
    if args.verbose:
        print('Done!')

    if args.samples:
        plt.figure(1)

    print_counter = 0
    counter = 0
    if args.verbose:
        print('Testing on %.2f%% of training data' % training_percent)
    start_time = datetime.datetime.now()
    for i, test_row in df_test_sample.iterrows():
        predictions = my_knn.knn(test_row[:-1], k_vals)
        for idx, k_val in enumerate(k_vals):
            if predictions[idx] == test_row['label']:
                k_vals[k_val] += 1
        if args.samples:
            plt.subplot(2, 2, counter + 1, title=('Guess: ' + str(predictions[-1]) + ' Actual: ' + str(test_row['label'])))
            plt.imshow(np.asarray(test_row[:-1]).reshape(height, width), cmap="gray")
        else:
            if counter > df_test_sample.shape[0] * .95 and print_counter == 3:
                print('\t95% complete...')
                print_counter += 1
            elif counter > df_test_sample.shape[0] * .75 and print_counter == 2:
                print('\t75% complete...')
                print_counter += 1
            elif counter > df_test_sample.shape[0] * .5 and print_counter == 1:
                print('\t50% complete...')
                print_counter += 1
            elif counter > df_test_sample.shape[0] * .25 and print_counter == 0:
                print('\t25% complete...')
                print_counter += 1
        counter += 1
    testing_time = (datetime.datetime.now() - start_time).total_seconds()
    if args.verbose:
        print('Done!')

    selected_k = max(k_vals, key=k_vals.get)

    if args.file:
        print('%.1f%% [%d training, %d testing]' % (training_percent, df_train_sample.shape[0], df_test_sample.shape[0]), file=file)
        if len(k_vals) > 1:
            print('Correct Guesses by k-value: %s' % k_vals, file=file)
            print('Chosen k-value: %d' % selected_k, file=file)
        print('%d correct out of %d (%.2f%%).' % (k_vals.get(selected_k), df_test_sample.shape[0], float(k_vals.get(selected_k)) / df_test_sample.shape[0] * 100), file=file)
        print('Testing duration : %.2f seconds\nTesting Time per Test Sample: %.2f seconds\n\n' % (testing_time, testing_time / df_test_sample.shape[0]), file=file)
        file.close()
        print('Printed results to file %s' % filename)
    else:
        print('\n\nResults:')
        print('%.1f%% [%d training, %d testing]' % (training_percent, df_train_sample.shape[0], df_test_sample.shape[0]))
        if len(k_vals) > 1:
            print('Correct Guesses by k-value: %s' % k_vals)
            print('Chosen k-value: %d' % selected_k)
        print('%d correct out of %d (%.2f%%).' % (k_vals.get(selected_k), df_test_sample.shape[0], float(k_vals.get(selected_k)) / df_test_sample.shape[0] * 100))
        print('Testing duration : %.2f seconds\nTesting Time per Test Sample: %.2f seconds' % (testing_time, testing_time / df_test_sample.shape[0]))

    if args.samples:
        plt.show()
    return float(k_vals.get(selected_k)) / df_test_sample.shape[0] * 100


if __name__ == '__main__':
    main()
