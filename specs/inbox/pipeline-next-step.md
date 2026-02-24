# pipeline-next-step

## What I'm Seeing

When I run `factory run spec`, the agent processes work beautifully with
streaming output showing every file read, write, and decision. It finishes with
a summary like "spec-lifecycle processed and moved to tasks/review/." Then the
terminal returns to the prompt and I'm left wondering: what do I run next?

I know the pipeline order (spec → researcher → builder → verifier) but the CLI
doesn't tell me. I have to remember which agent comes next and whether there's
work waiting for it. After Builder finishes, I have to know to run Verifier. After
Spec finishes, I have to know to check if research is needed or if it went
straight to ready.

## What I Want to See

When an agent finishes and there's work in a downstream pipeline stage, the CLI
prints the next command to run. Something like:

```
  specs/ready/ has 1 file — next: factory run builder
```

If there's nothing downstream, it says so:

```
  Pipeline idle — nothing waiting downstream.
```

The operator always knows what to do next without having to inspect the
filesystem manually.
