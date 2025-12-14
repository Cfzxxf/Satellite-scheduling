from collections import deque

# ===== 第三方库 =====
import numpy as np
import tensorflow as tf


# -------------------------- 通用组件 --------------------------
class ReplayBuffer:
    """存储智能体的交互经验，并随机采样用于训练"""

    def __init__(self, capacity: int = 5000):
        self.buffer = deque(maxlen=capacity)

    def add(self, state, action_index: int, reward: float, next_state, done: bool):
        self.buffer.append((state, action_index, reward, next_state, done))

    def sample(self, batch_size: int):
        idx = np.random.choice(len(self.buffer), batch_size, replace=False)
        return [self.buffer[i] for i in idx]

    def size(self) -> int:
        return len(self.buffer)


@tf.function
def train_step(
    model,
    target_model,
    optimizer,
    loss_fn,
    states,
    actions,
    rewards,
    next_states,
    dones,
    gamma: float,
):
    """
    标准 DQN 一步更新：
    - 使用 target_model 计算下一状态最大 Q
    - 使用 TD 目标更新当前网络
    """
    target_q = target_model(next_states)
    max_target_q = tf.reduce_max(target_q, axis=1)
    batch_indices = tf.range(tf.shape(actions)[0])
    full_indices = tf.stack([batch_indices, actions], axis=1)

    updated_q = tf.where(
        tf.cast(dones, tf.bool), rewards, rewards + gamma * max_target_q
    )

    with tf.GradientTape() as tape:
        q_pred = model(states)
        q_selected = tf.gather_nd(q_pred, full_indices)
        loss = loss_fn(updated_q, q_selected)

    grads = tape.gradient(loss, model.trainable_variables)
    optimizer.apply_gradients(zip(grads, model.trainable_variables))
    return loss  # 返回损失值用于监控


class MaxMetric:
    """记录区间最大值"""

    def __init__(self, name: str = "max_metric"):
        self.max_value = float("-inf")
        self.name = name

    def update_state(self, value: float):
        self.max_value = max(self.max_value, value)

    def result(self) -> float:
        return self.max_value

    def reset_states(self):
        self.max_value = float("-inf")
