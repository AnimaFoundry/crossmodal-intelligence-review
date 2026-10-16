# From Synaesthetic Metaphor to Crossmodal Intelligence

## Evidence, Identifiability, and Lessons from Evolution

**AnimaFoundry · Review preprint v1.0.0 · 16 October 2026 · Not peer reviewed**

This English critical integrative review examines when heterogeneous sensory observations support useful crossmodal learning. It distinguishes rhetoric and human synaesthesia from functional machine capabilities, connects sensor diversity to identifiability, and evaluates bounded analogies to mutation, adaptation, and predator-prey dynamics.

- [Read the PDF](paper.pdf)
- [Read the linked text](paper.md)
- [Review methods and limitations](METHODS.md)
- [49-source evidence ledger](references.json)
- [Source and rights record](SOURCE_AND_RIGHTS.md)
- [Release notes](RELEASE_NOTES.md)

The central hypothesis is conditional: aligned observations and discriminating physical variation may improve specified transfer tasks. More sensors, dimensions, noise, or mutation do not guarantee improvement. Machine-synesthesia terminology and crossmodal learning have extensive prior work, explicitly acknowledged here.

The release contains an original synthesis, five tables, an original schematic, six exact least-squares examples, and an unperformed contact-response study proposal. It includes no new biological, human, hardware, or trained-model experiment. Artifact checks do not constitute scientific replication or peer review. The paper is a separate preprint, not a software-product or invention delivery.

The earlier companion review is [Low-Power Sensing for an Internet of Intelligence](https://github.com/AnimaFoundry/internet-of-intelligence-review). This article adds a different question about information, learning, and analogy; it does not replace that paper.

## Reproduce the document and exact illustrations

Python 3.12 is used in CI. From this repository root:

```console
python -m pip install -r requirements.txt
python scripts/verify_paper.py
python scripts/identifiability_example.py --write
python scripts/build_paper.py --destination build/reproduced
python scripts/verify_paper.py --rebuild build/reproduced
```

The illustration script uses exact rational arithmetic and no external data or stochastic training. The PDF builder renders original text and diagram without fetching sources. The verifier checks citation consistency, exact algebra, publication hashes, PDF text, and reproduced page boundaries. These checks do not reproduce any cited study. Build dependencies are installed separately, not vendored.

## License and attribution

Original prose, tables, and diagram: CC BY 4.0. Helper scripts and workflow: MIT. See [LICENSE](LICENSE). Cited works retain their rights. No third-party article, figure, dataset, model weight, or private attachment is redistributed. The build tool adapts AnimaFoundry's earlier MIT-licensed review tooling. AI assistance is disclosed in the manuscript. No patent clearance or novelty opinion is claimed.

Corrections should identify the passage, source, and proposed change. Please distinguish document defects from empirical questions the review leaves open.
