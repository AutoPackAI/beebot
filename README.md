# BeeBot

BeeBot is your personal worker bee, an Autonomous AI Assistant designed to perform a wide range of practical tasks
autonomously.

## Philosophy

BeeBot's development process is guided by a specific philosophy, emphasizing key principles that shape its development
and future direction.

### Priorities

The development of BeeBot is driven by the following priorities:

1. Functionality: BeeBot aims to achieve a high success rate for tasks within its range of expected capabilities.
2. Flexibility: BeeBot strives to be adaptable to a wide range of tasks, expanding its range over time.
3. Reliability: BeeBot focuses on reliably completing known tasks with predictability.
4. Efficiency: BeeBot aims to execute tasks with minimal steps, optimizing both time and resource usage.
5. Convenience: BeeBot aims to provide a user-friendly platform for task automation.

### Principles

To achieve these priorities, BeeBot follows the following principles:

- Tool-focused: BeeBot carefully selects and describes tools, ensuring their reliable use by LLMs. It
  will utilize [AutoPack](https://autopack.ai) as the package manager for its tools.
- LLM specialization: BeeBot will leverage a variety of LLMs best suited for different tasks, while OpenAI remains the
  primary LLM for planning and decision-making.
- Functionality and reliability first: BeeBot prioritizes functionality and reliability over developer quality-of-life,
  which may limit support for specific platforms.
- Unorthodox methodologies: BeeBot employs unconventional development approaches to increase development speed, such as
  the absence of unit tests.
- Proven concepts: BeeBot adopts new concepts only after they have been proven to enhance its five priorities.
  As a result, it does not have complex memory or a tree of thought.

### Status

BeeBot is currently a work in progress and an early stage research project. Its focus is not on production usage at this
time.

## Installation

To get started with BeeBot, you can install it on your local machine using Python. Please note that BeeBot is still
under active development, and its dependencies and requirements may change.

```bash
git clone https://github.com/AutoPackAI/beebot.git
cd beebot
poetry install
```

## Running

Currently, you can run BeeBot using the CLI:

```bash
python beebot/initiator/cli.py --task "Write 'hello world' to hi.txt"
```

Please note that while the CLI is the only available method at this time, here are some future plans:

- API: Will probably use [e2b](https://www.e2b.dev/).
- Web Interface: We are working on a web interface using Node.js (Remix)

## Documentation

For further information on the architecture and future plans of BeeBot, please refer to the `docs/` directory. The
documentation is currently very light, but will evolve alongside the project as new insights and developments emerge.
Contributions and feedback from the community are highly appreciated.