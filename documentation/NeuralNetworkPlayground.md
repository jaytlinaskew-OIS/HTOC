# Neural Network Playground – README & Tuning Guide

# Neural Network Playground – README & Tuning Guide

> **Neural Network Playground** is an interactive web-based tool by TensorFlow that helps you visually understand how neural networks learn and generalize. It provides an intuitive interface to experiment with datasets, features, and neural network architectures.

[Try It Here](https://playground.tensorflow.org)

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Tunable Parameters](#tunable-parameters)
    - [Neural Network Architecture](#neural-network-architecture)
    - [Input Features](#input-features)
    - [Dataset Options](#dataset-options)
    - [Training Settings](#training-settings)
    - [Regularization](#regularization)
3. [Tips & Tricks for Tuning](#tips--tricks-for-tuning)
4. [Example Configurations](#example-configurations)
5. [Common Pitfalls](#common-pitfalls)
6. [Educational Uses](#bonus-educational-uses)

---

## Getting Started

1. Open [playground.tensorflow.org](https://playground.tensorflow.org).
2. Choose a dataset (e.g., spiral, circle, linear) to experiment with.
3. Select input features (e.g., `x₁`, `x₂`, `x₁²`, `sin(x₁)`) to define the input space.
4. Build your neural network architecture by adding layers and neurons to model the data.
5. Tune hyperparameters such as learning rate, activation functions, and regularization techniques.
6. Hit ▶️ to train the model and visualize how it learns and generalizes in real time.

*Tip: Experiment with different datasets and features to observe how the decision boundary evolves and adapts.*

---

## Tunable Parameters

### Neural Network Architecture

| Parameter              | Description                                | Typical Use                               |
|------------------------|--------------------------------------------|-------------------------------------------|
| **# Hidden Layers**    | Layers between input and output            | More layers capture complex patterns but may increase training time and risk overfitting. Start with 1-2 layers for simpler tasks. |
| **# Neurons per Layer**| Width of each layer                        | More neurons = more expressive model, but too many can lead to overfitting. Start with 4-8 neurons per layer and adjust as needed. |
| **Activation Function**| Non-linearity applied to each neuron       | Choose based on task and complexity. Common choices include `ReLU` for speed, `Tanh` for bounded outputs, and `Sigmoid` for probabilistic tasks. |

#### Common Activation Functions

| Activation | Use When...                     | Pros              | Cons                    |
|------------|----------------------------------|-------------------|-------------------------|
| `ReLU`     | Fast training, simple structure  | Sparse, fast      | Can die (zero gradients)|
| `Tanh`     | Inputs/outputs in [-1, 1]        | Smooth, bounded   | Slower convergence      |
| `Sigmoid`  | Binary or probabilistic outputs  | Probabilistic     | Vanishing gradients     |
| `Linear`   | Regression tasks                 | No transformation | Can't model non-linearities |

*Tip: Start with a simple architecture (e.g., 1 hidden layer with 4 neurons) and gradually increase complexity as needed.*

---

### Input Features

| Feature         | Description                                | When to Use                              |
|-----------------|--------------------------------------------|------------------------------------------|
| `x₁`, `x₂`       | Raw coordinate input features              | Basic datasets like linear or Gaussian   |
| `x₁²`, `x₂²`     | Quadratic terms (good for circular data)  | Circular or radial patterns              |
| `x₁ * x₂`       | Feature interaction                        | Complex relationships like XOR           |
| `sin(x₁)`, `sin(x₂)` | Periodic or wave-like pattern modeling | Spiral or periodic datasets              |

*Tip: Use engineered features like `x₁ * x₂` or `sin(x₁)` to improve performance on nonlinear datasets.*

---

### Dataset Options

| Dataset  | Pattern          | Challenge                    | Suggested Features                       |
|----------|------------------|------------------------------|------------------------------------------|
| Circle   | Ring vs center   | Requires quadratic features  | `x₁²`, `x₂²`                             |
| Spiral   | Twisting arms    | High complexity              | `x₁`, `x₂`, `sin(x₁)`, `x₁ * x₂`         |
| XOR      | Checkerboard     | Non-linear separability      | `x₁`, `x₂`, `x₁ * x₂`                    |
| Gaussian | Two clusters     | Easier separation task       | `x₁`, `x₂`                               |
| Linear   | Straight line    | Basic classifier tuning      | `x₁`, `x₂`                               |

*Tip: Start with simpler datasets like Linear or Gaussian before tackling more complex ones like Spiral.*

---

### Training Settings

| Parameter        | Description                        | Typical Range     | Impact on Training                     |
|------------------|------------------------------------|-------------------|-----------------------------------------|
| **Learning Rate**| Speed of weight updates            | `0.01 – 0.3`      | Higher values speed up training but risk divergence |
| **Batch Size**   | Number of samples per step         | `1`, `10`, `All`  | Smaller batches add noise, larger batches stabilize |
| **Noise**        | Adds randomness to labels          | `0% – 50%`        | Simulates real-world noisy data         |
| **Epochs**       | Training cycles (use play button)  | Set via controls  | More epochs allow longer training       |

*Tip: Start with a learning rate of `0.03` or `0.1`. Adjust based on how the loss evolves.*

---

### Regularization

| Type   | When to Use                      | Effect                   | Typical Rate         |
|--------|----------------------------------|--------------------------|----------------------|
| None   | Clean data, simple model         | No penalty               | `0`                  |
| L1     | Force model simplicity (sparse)  | Zeroes out less useful weights | `0.01 – 0.1`         |
| L2     | Penalize large weights           | Smooths the model        | `0.01 – 0.1`         |

*Tip: Use L2 regularization when working with noisy data or large networks to prevent overfitting.*

---

## Tips & Tricks for Tuning

| Tip                                    | Why It Helps                           |
|----------------------------------------|----------------------------------------|
| Start simple (1 layer, 4 neurons)      | Understand learning behavior            |
| Add complexity gradually               | Avoid overfitting early                 |
| Use `Tanh` or `ReLU` activations       | Nonlinear power                        |
| Add L2 regularization if overfitting   | Keeps model weights in check           |
| Use more features for non-linear data  | Helps model complex boundaries         |
| Watch the decision boundary animation  | Visualize how your network learns      |

*Tip: Regularly monitor the loss curve and decision boundary to diagnose issues like overfitting or underfitting.*

---

## Example Configurations

### 1. Learn Spiral (Challenging Pattern)
- **Dataset**: Spiral  
- **Features**: `x₁`, `x₂`, `x₁ * x₂`, `sin(x₁)`  
- **Layers**: 3 hidden layers × 6 neurons  
- **Activation**: `Tanh`  
- **Learning Rate**: `0.03`  
- **Regularization**: L2 (`0.03`)  
- **Noise**: `10%`  

### 2. Simple Linear Classifier (Easy)
- **Dataset**: Linear  
- **Features**: `x₁`, `x₂`  
- **Layers**: 1 hidden layer × 4 neurons  
- **Activation**: `ReLU`  
- **Learning Rate**: `0.1`  
- **Regularization**: None  
- **Noise**: `0%`  

---

## Common Pitfalls

| Problem                        | Cause                          | Fix                          |
|-------------------------------|--------------------------------|-------------------------------|
| Model doesn't learn           | Learning rate too low          | Try `0.03` or `0.1`           |
| Decision boundary is chaotic  | Overfitting                    | Reduce neurons, add L2        |
| Boundary is too simple        | Underfitting                   | Add more layers or neurons    |
| Loss spikes wildly            | Learning rate too high         | Reduce it (e.g., `0.01`)      |

*Tip: If the model is unstable, try reducing the learning rate or simplifying the architecture.*

---

## Bonus: Educational Uses

Neural Network Playground is perfect for:
- Teaching core ML concepts visually
- Exploring model capacity and decision boundaries
- Demonstrating overfitting vs underfitting
- Building intuition for tuning hyperparameters **before coding anything**

---

Happy experimenting!  
Need help simulating your real model or turning this into a notebook? Let me know!
