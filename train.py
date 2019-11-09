import time
import sys
import flow
import plac
import tensorflow as tf
import segmentation_models as sm
import tensorflow.keras as keras
import numpy as np
import logging
logger = logging.getLogger(__name__)


callbacks = [
    keras.callbacks.ModelCheckpoint('./best_model.hdf5', save_weights_only=True, save_best_only=True),
]

BATCH_SIZE = 1
metrics = ['sparse_categorical_accuracy', sm.losses.CategoricalFocalLoss(), sm.metrics.IOUScore(), sm.metrics.FScore()]
#preprocess_input = sm.get_preprocessing(flow.BACKBONE)


def save_model(model, save_path="model-%s.hdf5" % flow.BACKBONE, pause=0):
    if pause > 0:
        sys.stderr.write("Saving in")
        for i in list(range(1,6))[::-1]:
            sys.stderr.write(" %d...\n" % i)
            time.sleep(pause)
    sys.stderr.write("Saving...\n")
    return model.save_weights(save_path)


def load_weights(model, save_path="model-%s.hdf5" % flow.BACKBONE):
    try:
        model.load_weights(save_path)
        logger.info("Model file %s loaded successfully." % save_path)
    except OSError as exc:
        sys.stderr.write("!! ERROR LOADING %s:" % save_path)
        sys.stderr.write(str(exc) + "\n")
    return model


def build_model():
    return sm.Unet(flow.BACKBONE, classes=flow.N_CLASSES,
                   input_shape=flow.SAMPLESHAPE, activation='softmax',
                   encoder_weights='imagenet')


def main(save_path="model-%s.hdf5" % flow.BACKBONE,
         optimizer='adam',
         loss='sparse_categorical_crossentropy',
         restore=True,
         verbose=1,
         epochs=50):
    logger.info("Building model.")
    model = build_model()
    if restore:
        load_weights(model)

    sm.utils.set_trainable(model, recompile=False)
    model.compile(optimizer=optimizer, loss=loss, metrics=metrics)

    logger.info("Creating dataflows.")
    train_seq = flow.Dataflow(batch_size=BATCH_SIZE)#, transform=0.30)
    val_seq = flow.Dataflow(batch_size=BATCH_SIZE, validation_set=True)

    logger.info("Training.")
    train_step(model, train_seq, verbose, epochs, callbacks, save_path, val_seq)
    save_model(model, save_path)


def train_step(model, train_seq, verbose, epochs, callbacks, save_path, val_seq):
    try:
        model.fit(train_seq, validation_data=val_seq, epochs=epochs,
                            verbose=verbose, callbacks=callbacks)
    except KeyboardInterrupt:
            save_model(model, save_path, pause=1)
            sys.exit()
    except Exception as exc:
        save_model(model, save_path)
        raise(exc)


def train_step_generator(model, train_seq, verbose, epochs, callbacks, save_path, val_seq=None):
    try:
        model.fit_generator(train_seq, validation_data=val_seq, epochs=epochs,
                            verbose=verbose, callbacks=callbacks)
    except KeyboardInterrupt:
            save_model(model, save_path, pause=1)
            sys.exit()
    except Exception as exc:
        save_model(model, save_path)
        raise(exc)

if __name__ == "__main__":
    plac.call(main)
