# BeeBot

## Introduction

BeeBot is an Autonomous AI Assistant is designed to perform a range of tasks autonomously, taking high-level
instructions from human users and transforming them into actions which are then performed. BeeBot's capabilities are
based on the underlying components: Planner, Decider, Executor, and Body. These components work in unison, each
fulfilling its part in a state machine-driven process.

## Major Components

### Planner

The Planner is responsible for taking the human task and the previous outputs, and creating a Plan object for it. This
is done through an LLM that can interpret the requirements of the task and the context provided by
previous outputs. The Planner thus plays a vital role in interpreting and organizing tasks, setting the stage for their
execution.

### Decider

Once a Plan has been generated, the Decider takes over. It assesses the Plan and makes a Decision, again through the
LLM, about what action the system should take next. The Decision maps to exactly one function call.

### Executor

The Executor is the "action" component of the system. Once a Decision has been made about the next step, the Executor
takes this Decision and performs the necessary action. It also creates an Observation based on the results of the
action. This Observation is a structured record of what occurred during execution.

### Body

The Body is a container for the Planner, Decider, and Executor components. It also holds memories and
configuration settings that help the Assistant adapt and optimize its functioning. The Body manages the data flow
between the other components and also holds the State Machine that governs the operation of the entire system.

## Operational Workflow (State Machine)

```
[ Setup ]
    |
    | start
    v
[ Starting ]
    |
    | plan
    v
[ Planning ] <--------+
    |                 |
    | wait            |
    v                 |
[ Waiting ]           |
    |                 |
    | decide          |
    v                 |
[ Deciding ]          |
    |                 | plan (Cycle Loop)
    | wait            |
    v                 |
[ Waiting ]           |
    |                 |
    | execute         |
    v                 |
[ Executing ]         |
    |                 |
    | wait            |
    v                 |
[ Waiting ] ----------+
    |
    | finish
    v
[ Done ]
```

These state transitions are governed by events or conditions such as `start`, `plan`, `decide`, `execute`, `wait`,
and `finish`. These dictate how the Assistant moves from one state to the next, and how the Planner, Decider, and
Executor components interact.