# Recording pack format (normative)

A recording pack records one asynchronous actor-learner training run. Every bundle directory
under `/app/recordings` holds the files below. This document is normative for field meanings.

## `manifest.json`

| field | meaning |
| --- | --- |
| `bundle` | bundle identifier, reproduced verbatim in the pulse ledger |
| `gamma` | discount factor |
| `n_step` | maximum segment length in transitions |
| `n_actions` | size of the discrete action set, actions are integers in `[0, n_actions - 1]` |
| `feature_dim` | length of every observation feature vector |
| `buffer_capacity` | number of slots in the learner's circular transition buffer |
| `batch_size` | number of draws the learner makes per learner step |
| `learner_steps` | number of learner steps in the run, indexed `0` to `learner_steps - 1` |
| `target_refresh_interval` | learner steps between target parameter refreshes |
| `visibility_lag` | non-negative integer learner steps the learner waits past each ingest entry's recorded `step` before that entry becomes effective |
| `register_delay` | non-negative integer learner steps a fully admitted segment must wait before it may enter the priority ledger |
| `sampler_priority_lag` | when greater than zero, draws use the post-writeback priority vector from the previous learner step |
| `alpha` | priority exponent |
| `beta` | importance sampling exponent for the replay correction |
| `priority_eps` | additive floor inside the priority expression |
| `rho_bar` | clip bound for the policy gradient importance ratio |
| `c_bar` | clip bound for the trace cutting importance ratio |
| `sampler_seed` | seed for the priority proportional sampler |

## `features.json`

Object mapping every observation identifier to its feature vector, a list of
`feature_dim` floats. Every `obs_id` and every non null `cut_obs_id` appearing in the
shards is present as a key.

## `params/epoch-NN.json`

One file per target refresh epoch, `NN` being the zero padded epoch index starting at
`00`. Epoch indices are contiguous. Each file holds a linear value head and a linear
policy head evaluated on observation features:

- `value_w`: list of `feature_dim` floats
- `value_b`: float
- `policy_w`: list of `n_actions` lists of `feature_dim` floats
- `policy_b`: list of `n_actions` floats

The value of an observation under an epoch is the affine map `value_w . feat + value_b`.
The current policy log probability of an action under an epoch is the log softmax over
the `n_actions` logits `policy_w[a] . feat + policy_b[a]`, taken at the recorded action.

## `shards/actor-NN.jsonl`

One JSON object per line, one file per actor. Lines within a file are ascending in `seq`.

| field | meaning |
| --- | --- |
| `seq` | global admission sequence number, unique across the whole bundle |
| `actor_id` | actor that produced the transition |
| `episode_id` | episode the transition belongs to, unique across the whole bundle |
| `t` | offset of the transition inside its episode, starting at `0` and contiguous |
| `obs_id` | observation the action was taken from |
| `action` | recorded action index |
| `behavior_logp` | log probability the behavior policy assigned to `action` |
| `reward` | reward received for the transition |
| `terminated` | true when the environment reached a terminal state on this transition |
| `truncated` | true when the episode was cut by a time limit on this transition |
| `cut_obs_id` | observation recorded after a time limit cut, non null exactly when `truncated` is true, otherwise null |

`terminated` and `truncated` are never both true. Every episode ends with exactly one
transition whose `terminated` or `truncated` is true, and that transition is the episode's
highest `t`.

## `ingest.json`

`{"admissions": [{"t": <int>, "seq_watermark": <int>}, ...]}`. Each entry records a
publication fact whose recorded `step` is the earliest learner step at which the fact
is eligible to become effective after adding the bundle `visibility_lag`. Once effective,
the learner can see every transition up to and including `seq_watermark`. Entries are not
required to be sorted and more than one entry may share a step.
