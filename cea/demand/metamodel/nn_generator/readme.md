
Prerequisites:
to run the neural net you will need a minimum of 100 GB of hardisk available
for every 100 samples of a city of 230 buildings. i.e., 1GB/sample.

Install theano like this:
conda install numpy scipy mkl-service libpython m2w64-toolchain nose nose-parameterized sphinx pydot-ng

 and meke sure to include: conda install m2w64-toolchain

The radiation file should be already generated.

To run do:
1. check the nn_settings.py file
2. run the scalar_sampler.py
3. run scaler_fit.py

4. Now there are two posibilities for starting the training:
4.1. the first is to generate x number of samples (100 in this example)
and then train the network (these samples will be constant in all epocs).
    - run nn_pretrainer_pipeline.py
4.2. the second is to randomly generate a smaller number of samples (max 10)
and train the NN (these 10 samples will be updated in each epoc).
    - run random_pipeline.py
5. Now there are two possibilities for continuing the training:
5.1. continue training based on 4.1.
    - run nn_pretrainer_continue.py
5.2. continue training based on 4.2.
    - run nn_trainer_continue.py
6. Evaluate the network (test the perforamnce based on a random sample)
6.1. you can evaluate based on a random sample
    - run nn_trainer_evaluate.py
6.2 you can estimate the outputs based on the current inputs of CEA.
    - run nn-trainer_estimate.py

