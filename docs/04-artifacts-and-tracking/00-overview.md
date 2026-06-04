# Artifacts and Tracking

In this section, we make model outputs persistent, inspectable, and traceable.

## What You Will Build

- local object storage
- artifact layout
- experiment tracking
- lineage record

## Why This Matters

A model file without context is not reproducible. A useful ML platform needs to answer: which data, code, parameters, image, and run produced this model?

## Acceptance Criteria

You are done with this section when:

- datasets, models, metrics, and reports are stored outside ephemeral pod filesystems
- each run records the key metadata needed for reproducibility
- KFP runs can be connected to experiment tracking runs
