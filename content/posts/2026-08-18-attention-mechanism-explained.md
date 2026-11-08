---
title: "The Attention Mechanism, Explained From First Principles"
description: "A ground-up walkthrough of scaled dot-product attention and multi-head attention, with the matrix shapes made explicit and a tiny NumPy implementation you can run yourself."
category: "Machine Learning"
tags: [AI, DeepLearning, LLM, Python]
featured: true
type: article
---

If you can multiply matrices, you can understand attention. Most explanations skip the boring part — the actual shapes flowing through the computation — and that's exactly the part that makes everything click. This post fills that gap with a working NumPy implementation, no framework required.

## The problem attention solves

A recurrent network reads a sequence one token at a time, so information from an early token has to survive many update steps before it can influence a late one. Attention removes that bottleneck: every position can look directly at every other position in a single step, weighted by how relevant they are to each other.

::: note
This post assumes you're comfortable with matrix multiplication and softmax. If either is rusty, the shapes below are worth tracing through with pen and paper once.
:::

## Queries, keys and values

Every input token is projected into three vectors:

- **Query ($q$)** — what this token is looking for
- **Key ($k$)** — what this token has to offer
- **Value ($v$)** — the actual content passed along if selected

For a sequence of length $n$ and model dimension $d$, we stack these into matrices $Q, K, V \in \mathbb{R}^{n \times d}$. Attention is then:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right)V$$

The $QK^\top$ term computes a similarity score between every query and every key — an $n \times n$ matrix. Dividing by $\sqrt{d_k}$ keeps those scores from growing too large as dimensionality increases, which would otherwise push softmax into a regime with vanishing gradients.

## A minimal implementation

```python
import numpy as np

def softmax(x, axis=-1):
    x = x - np.max(x, axis=axis, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=axis, keepdims=True)

def attention(Q, K, V):
    d_k = Q.shape[-1]
    scores = Q @ K.transpose(-1, -2) / np.sqrt(d_k)
    weights = softmax(scores, axis=-1)
    return weights @ V, weights

n, d = 4, 8
rng = np.random.default_rng(0)
Q, K, V = rng.normal(size=(n, d)), rng.normal(size=(n, d)), rng.normal(size=(n, d))

out, weights = attention(Q, K, V)
print(out.shape)     # (4, 8) — one output vector per input token
print(weights.shape) # (4, 4) — how much each token attends to every other token
```

::: example
Run this with `n = 1` and you'll see attention degrade to a single weighted average — there's nothing to "attend" to, so it just returns a scaled copy of `V`. That degenerate case is a useful sanity check when debugging a larger model.
:::

## Multi-head attention

A single attention operation only learns one notion of "relevance." Multi-head attention runs several attention operations in parallel, each with its own learned projections, then concatenates the results:

$$\text{MultiHead}(Q,K,V) = \text{Concat}(\text{head}_1, \dots, \text{head}_h)W^O$$

In practice this means splitting $d$ into $h$ smaller chunks (commonly $d_k = d / h$) so the total compute stays roughly constant while the model gains several independent "views" of the sequence — one head might track syntactic agreement, another might track coreference.

| Component | Shape | Purpose |
|---|---|---|
| $W^Q, W^K, W^V$ | $d \times d_k$ | Per-head projections |
| $QK^\top$ | $n \times n$ | Pairwise similarity scores |
| softmax output | $n \times n$ | Attention weights (rows sum to 1) |
| $W^O$ | $h \cdot d_k \times d$ | Recombines heads into model dimension |

## Where this goes next

Scaled dot-product attention is the core primitive inside every transformer block, paired with a feed-forward layer, residual connections and layer normalization. The next post in this series builds a full transformer block on top of the function above — same NumPy, no dependencies.

::: tip
If you want to see this trained rather than just wired up, swap the NumPy arrays for `torch.Tensor` and wrap `attention()` in an `nn.Module`; the math doesn't change, only the autograd does.
:::
