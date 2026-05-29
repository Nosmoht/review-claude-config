---
name: data-pipeline-orchestrator
description: >
  Orchestrates multi-stage data pipeline runs by reading pipeline
  configuration files, invoking stage executors in sequence, collecting
  stage outputs, and writing a consolidated run report. Use when the user
  asks to run, resume, or inspect a named data pipeline. Do not use for
  ad-hoc data transformations or single-stage processing tasks.
---

# Data Pipeline Orchestrator

## Overview

The Data Pipeline Orchestrator skill coordinates the execution of multi-stage
data processing pipelines. A pipeline is a sequence of named stages, each
stage being a discrete data transformation unit that reads from an upstream
source and writes to a downstream sink. The orchestrator reads a declarative
pipeline configuration file, resolves stage dependencies, invokes each stage
executor in topological order, monitors stage completion, collects outputs,
aggregates run metadata, and finally writes a consolidated run report
summarising stage-level outcomes, data volumes, timing, and any errors or
warnings encountered during the run.

The skill is designed to be robust in the face of transient failures. If a
stage fails due to a transient error (network timeout, temporary resource
unavailability, rate-limit hit from an upstream API), the orchestrator applies
a backoff-and-retry strategy before declaring the stage failed. The retry
behaviour is configurable per stage via the pipeline configuration file; the
default retry limit is three attempts with exponential backoff starting at two
seconds. If all retry attempts are exhausted and the stage still has not
completed successfully, the orchestrator marks the stage as failed, records
the failure reason in the run report, and — depending on whether the failed
stage is on the critical path — either aborts the pipeline run or continues
with the remaining independent stages.

The skill also supports partial pipeline resumption. If a previous run was
interrupted before completion (for example due to a session timeout, an
unexpected process termination, or an operator-initiated cancellation), the
orchestrator can resume from the last successfully completed stage checkpoint
rather than restarting the pipeline from the beginning. Resumption is gated
on the presence of a valid checkpoint file written by the prior run; if no
checkpoint file exists or the checkpoint is corrupt, the orchestrator falls
back to a full restart and logs a warning to that effect.

## Inputs

The orchestrator expects the following inputs from the calling session:

- **Pipeline name**: a human-readable identifier corresponding to a pipeline
  configuration file located in the `pipelines/` directory of the repository.
  The configuration file must be named `<pipeline-name>.yaml` and must conform
  to the pipeline configuration schema described in the Configuration Schema
  section below.

- **Run mode** (optional, defaults to `full`): one of `full`, `resume`, or
  `dry-run`. In `full` mode the orchestrator starts the pipeline from the
  beginning, ignoring any existing checkpoint. In `resume` mode the
  orchestrator reads the checkpoint file and continues from the last completed
  stage. In `dry-run` mode the orchestrator validates the configuration file
  and prints the planned execution order without actually executing any stage.

- **Stage override** (optional): a comma-separated list of stage names. When
  provided, the orchestrator only executes the listed stages, skipping all
  others. This is useful for re-running a subset of stages after fixing a
  configuration error or data issue without re-executing the full pipeline.

- **Verbosity level** (optional, defaults to `normal`): controls the amount of
  detail written to the run report. Accepted values are `quiet`, `normal`, and
  `verbose`. In `quiet` mode only stage-level pass/fail outcomes and the
  overall run status are recorded. In `normal` mode timing and data volume
  metrics are also included. In `verbose` mode the orchestrator additionally
  captures the first 500 lines of stdout from each stage executor and appends
  them to the run report as stage execution logs.

## Configuration Schema

Each pipeline configuration file is a YAML document with the following
top-level keys:

```yaml
name: <string>           # human-readable pipeline name
version: <semver>        # schema version; currently "1.0.0"
stages:
  - id: <string>         # unique stage identifier within the pipeline
    executor: <string>   # path to the stage executor script relative to repo root
    depends_on: [...]    # list of stage ids that must complete before this stage
    retry:
      limit: <int>       # maximum retry attempts (default 3)
      backoff_seconds: <int>  # base backoff duration in seconds (default 2)
    timeout_seconds: <int>   # per-stage timeout; 0 means no timeout (default 0)
    inputs:
      - source: <string> # upstream data source path or URI
        format: <string> # data format (csv, parquet, json, jsonl, avro)
    outputs:
      - sink: <string>   # downstream data sink path or URI
        format: <string> # data format
checkpoints:
  directory: <string>    # directory where checkpoint files are written (default .checkpoints/)
reporting:
  directory: <string>    # directory where run reports are written (default .reports/)
  format: <string>       # report format: markdown, json, or both (default markdown)
```

The `stages` array defines the processing units. Each stage must have a unique
`id` value. The `depends_on` array encodes the dependency graph; the
orchestrator performs a topological sort to determine execution order. If the
dependency graph contains a cycle, the orchestrator aborts immediately with an
error indicating which stage IDs form the cycle.

The `executor` field names a path to a script file that the orchestrator will
invoke to perform the stage's data transformation. The script is called with a
fixed set of environment variables and command-line arguments that supply the
stage inputs and outputs; the executor is expected to exit with code 0 on
success and a non-zero code on failure.

The `retry` block is optional and defaults to three attempts with two-second
base backoff. The orchestrator applies exponential backoff: the wait time
before the k-th retry is `backoff_seconds * (2 ** (k-1))` seconds. For example
with the default settings the first retry happens after 2 seconds, the second
after 4 seconds, and the third after 8 seconds.

The `timeout_seconds` field is also optional. When set to a positive integer
the orchestrator kills the executor process if it has not completed within the
specified number of seconds and records a timeout failure. When set to 0 (the
default) no timeout is applied.

## Execution Steps

### Step 1 — Locate and load the pipeline configuration

The orchestrator begins by resolving the pipeline name supplied by the user to
a configuration file path. It looks in the `pipelines/` directory for a file
named `<pipeline-name>.yaml`. If the file does not exist the orchestrator
reports an error and stops. If the file exists the orchestrator loads it and
validates it against the configuration schema using a built-in YAML schema
validator. Any validation errors are reported with the specific field path and
the violated constraint. The orchestrator does not attempt to execute a
pipeline whose configuration file fails validation.

After the configuration is loaded the orchestrator reads the `version` field
and checks it against the supported schema versions. The current implementation
supports schema version `1.0.0` only. If the configuration declares a different
schema version the orchestrator logs a warning and continues, but flags the run
report with a schema version mismatch notice so the operator is aware that
behaviour may differ from the documented contract.

### Step 2 — Resolve the dependency graph

With the configuration loaded the orchestrator extracts the `stages` array and
constructs a directed acyclic graph (DAG) where each node is a stage ID and
each directed edge represents a dependency. The orchestrator then runs a
topological sort (Kahn's algorithm) on the DAG to determine the execution
order. If the sort detects a cycle (i.e. not all nodes can be placed in the
sorted order), the orchestrator identifies the participating nodes, formats an
error message listing the cycle members, and aborts.

The resolved execution order is logged at the start of the run report under a
"Planned Execution Order" heading so that operators can verify the orchestrator
interpreted the dependency graph correctly before examining stage-level
outcomes.

### Step 3 — Check for an existing checkpoint (resume mode only)

In `resume` mode the orchestrator looks for a checkpoint file in the directory
specified by `checkpoints.directory` (defaulting to `.checkpoints/`). The
checkpoint file is named `<pipeline-name>.checkpoint.json`. If the file is
found the orchestrator loads it and extracts the list of stage IDs that were
marked as completed in the prior run. Any stage in the completed list is
skipped in the current run, allowing execution to continue from where it left
off.

If the checkpoint file is not found in resume mode the orchestrator logs a
warning: "No checkpoint found for pipeline '<pipeline-name>'; starting from
the beginning." and proceeds as if run mode were `full`. This ensures that a
resume request on a pipeline with no prior checkpoint does not silently produce
a duplicate full run with a misleading label.

The checkpoint file itself is a JSON document with the following structure:

```json
{
  "pipeline": "<pipeline-name>",
  "run_id": "<uuid>",
  "completed_stages": ["stage-a", "stage-b"],
  "started_at": "<ISO-8601 timestamp>",
  "last_updated_at": "<ISO-8601 timestamp>"
}
```

The `completed_stages` array is the sole authoritative source of truth for
resume decisions. The `started_at` and `last_updated_at` timestamps are
recorded for observability only and do not affect orchestrator behaviour.

### Step 4 — Execute stages in topological order

The orchestrator iterates through the topologically sorted stage list. For each
stage that has not been skipped (either because it was completed in a prior
run or because it is not in the user-supplied stage override list), the
orchestrator:

1. Verifies that all stages listed in `depends_on` have completed successfully
   in the current run. If any dependency failed or was skipped, the orchestrator
   skips the current stage and records a dependency-failure skip reason in the
   run report.

2. Invokes the stage executor with the following environment variables set:
   - `PIPELINE_NAME` — the pipeline name
   - `STAGE_ID` — the stage ID
   - `STAGE_INPUTS` — a JSON-encoded array of input source descriptors
   - `STAGE_OUTPUTS` — a JSON-encoded array of output sink descriptors
   - `RUN_ID` — a UUID generated at the start of the pipeline run

3. Monitors the executor process. If `timeout_seconds` is positive and the
   executor has not exited within that many seconds, the orchestrator sends
   SIGTERM to the process and waits up to five additional seconds. If the
   process does not exit within five seconds after SIGTERM, the orchestrator
   sends SIGKILL. Either way a timeout failure is recorded for the stage.

4. If the executor exits with a non-zero code the orchestrator applies the
   retry policy. Between retry attempts the orchestrator writes a progress note
   to the checkpoint file so that a subsequent resume can observe whether a
   retry is in progress.

5. If all retry attempts are exhausted the orchestrator marks the stage as
   failed, records the exit code and the last 100 lines of stderr in the run
   report, and evaluates whether the failed stage is on the critical path of
   any downstream stage. If it is, the orchestrator aborts the run. If it is
   not, execution continues with the remaining independent stages.

6. If the executor exits with code 0 the orchestrator marks the stage as
   completed, records timing and any reported data volume metrics, and updates
   the checkpoint file.

### Step 5 — Write the run report

After all stages have been executed (or skipped or failed), the orchestrator
composes the run report. The report includes the following sections regardless
of verbosity level:

- **Run summary**: pipeline name, run ID, run mode, start time, end time,
  total duration, overall status (Success, PartialFailure, or Failure).
- **Planned execution order**: the topologically sorted list of stage IDs.
- **Stage outcomes**: a table with one row per stage showing stage ID,
  status (Completed, Failed, Skipped), duration, data input volume, data
  output volume, and retry count.

In `normal` verbosity mode the following additional sections are included:

- **Timing breakdown**: a bar chart (ASCII) of stage durations to facilitate
  quick identification of bottleneck stages.
- **Data volume summary**: total bytes read and written across all stages,
  broken down by data format.

In `verbose` verbosity mode the following additional sections are also
included:

- **Stage execution logs**: for each stage, the first 500 lines of the
  executor's stdout are appended under a collapsible heading.

The run report is written to the directory specified by `reporting.directory`
(defaulting to `.reports/`) in the format specified by `reporting.format`
(defaulting to `markdown`). The file name is
`<pipeline-name>-<run-id>-<timestamp>.md` (or `.json` for JSON format, or
both files for `both` format).

Once the run report is written the orchestrator prints a one-line summary to
the user session: "Pipeline '<pipeline-name>' run <status> — report written to
<report-path>." If the overall run status is Failure the orchestrator also
lists the names of the failed stages so the user can immediately identify which
stages need attention.

## Error Handling

The orchestrator distinguishes five error classes:

- **ConfigurationError**: the pipeline configuration file is missing, cannot
  be parsed, or fails schema validation. The orchestrator aborts immediately
  and reports the specific validation failure without executing any stage.

- **DependencyCycleError**: the stage dependency graph contains a cycle. The
  orchestrator aborts immediately and lists the stage IDs involved in the cycle.

- **StageTimeoutError**: a stage executor did not complete within the
  configured timeout. After the timeout the executor is terminated and the
  stage is marked as failed with reason "timeout".

- **StageExecutorError**: a stage executor exited with a non-zero code after
  all retry attempts were exhausted. The stage is marked as failed with the
  exit code and the last 100 lines of stderr recorded in the run report.

- **CheckpointCorruptError**: the checkpoint file exists but cannot be parsed
  or does not conform to the expected structure. The orchestrator logs a
  warning, discards the checkpoint, and falls back to a full run.

For each error class the orchestrator constructs a structured error entry
containing the error class name, the affected stage ID (where applicable), the
human-readable error message, and any relevant diagnostic detail (exit code,
timeout duration, cycle members, validation path). These structured entries are
written to the run report under an "Errors and Warnings" section that always
appears at the end of the report regardless of verbosity level.

## Output Format

The skill outputs a one-line confirmation message after the run completes:

```
Pipeline '<pipeline-name>' <status> — report at <report-path>
```

Where `<status>` is one of: `succeeded`, `completed with failures`, or
`failed`. The `<report-path>` is the absolute path to the written run report
file. If the run was a dry-run, the output instead reads:

```
Dry-run complete — planned execution order: [<stage-ids>]
```

No other output is produced by default. If the user asks for verbose output
or inspects the run report directly they will find the detailed information
described in the Run Report section above.

## Notes

This skill does not modify source data. All data transformations are delegated
to stage executor scripts defined in the pipeline configuration. The
orchestrator's role is coordination, retry management, checkpointing, and
reporting. The executor scripts are outside the scope of this skill.

The skill assumes that the repository has a `pipelines/` directory containing
at least one pipeline configuration file. If the directory does not exist the
skill reports an error and stops. If the directory exists but contains no
matching configuration file the skill reports an error listing the available
pipeline names (derived from the YAML filenames in the directory) so the user
can correct the pipeline name supplied.
