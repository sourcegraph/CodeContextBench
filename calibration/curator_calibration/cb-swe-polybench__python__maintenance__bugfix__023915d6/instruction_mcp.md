# IMPORTANT: Source Code Access

**Local source files are not present.** Your workspace does not contain source code. You **MUST** use Sourcegraph MCP tools to discover, read, and understand code before making any changes.

**Target Repositories (version-pinned mirrors):**

- `github.com/sg-evals/transformers--45b70384` — use `repo:^github.com/sg-evals/transformers--45b70384$` filter

Scope ALL keyword_search/nls_search queries to these repos.
Use the repo name as the `repo` parameter for read_file/go_to_definition/find_references.


## Required Workflow

1. **Search first** — Use MCP tools to find relevant files and understand existing patterns
2. **Read remotely** — Use `sg_read_file` to read full file contents from Sourcegraph
3. **Edit locally** — Use Edit, Write, and Bash to create or modify files in your working directory
4. **Verify locally** — Run tests with Bash to check your changes

## Tool Selection

| Goal | Tool |
|------|------|
| Exact symbol/string | `sg_keyword_search` |
| Concepts/semantic search | `sg_nls_search` |
| Trace usage/callers | `sg_find_references` |
| See implementation | `sg_go_to_definition` |
| Read full file | `sg_read_file` |
| Browse structure | `sg_list_files` |
| Find repos | `sg_list_repos` |
| Search commits | `sg_commit_search` |
| Track changes | `sg_diff_search` |
| Compare versions | `sg_compare_revisions` |

**Decision logic:**
1. Know the exact symbol? → `sg_keyword_search`
2. Know the concept, not the name? → `sg_nls_search`
3. Need definition of a symbol? → `sg_go_to_definition`
4. Need all callers/references? → `sg_find_references`
5. Need full file content? → `sg_read_file`

## Scoping (Always Do This)

```
repo:^github.com/ORG/REPO$           # Exact repo (preferred)
repo:github.com/ORG/                 # All repos in org
file:.*\.ts$                         # TypeScript only
file:src/api/                        # Specific directory
```

Start narrow. Expand only if results are empty.

## Efficiency Rules

- Chain searches logically: search → read → references → definition
- Don't re-search for the same pattern; use results from prior calls
- Prefer `sg_keyword_search` over `sg_nls_search` when you have exact terms
- Read 2-3 related files before synthesising, rather than one at a time
- Don't read 20+ remote files without writing code — once you understand the pattern, start implementing

## If Stuck

If MCP search returns no results:
1. Broaden the search query (synonyms, partial identifiers)
2. Try `sg_nls_search` for semantic matching
3. Use `sg_list_files` to browse the directory structure
4. Use `sg_list_repos` to verify the repository name

---

# Fix: SWE-PolyBench__python__maintenance__bugfix__023915d6

**Repository:** github.com/sg-evals/transformers--45b70384 (mirror of huggingface/transformers)
**Language:** python
**Category:** contextbench_cross_validation

## Description

`YolosImageProcessor` violates `longest_edge` constraint for certain images
### System Info

- `transformers` version: 4.35.0
- Platform: Linux-5.15.120+-x86_64-with-glibc2.35
- Python version: 3.10.12
- Huggingface_hub version: 0.17.3
- Safetensors version: 0.4.0
- Accelerate version: not installed
- Accelerate config: not found
- PyTorch version (GPU?): 2.1.0+cu118 (False)
- Tensorflow version (GPU?): 2.14.0 (False)
- Flax version (CPU?/GPU?/TPU?): 0.7.4 (cpu)
- Jax version: 0.4.16
- JaxLib version: 0.4.16
- Using GPU in script?: no
- Using distributed or parallel set-up in script?: no

### Who can help?

@NielsRogge @amyeroberts 

### Information

- [ ] The official example scripts
- [ ] My own modified scripts

### Tasks

- [ ] An officially supported task in the `examples` folder (such as GLUE/SQuAD, ...)
- [ ] My own task or dataset (give details below)

### Reproduction


```py
from transformers import AutoProcessor
from PIL import Image
import requests

processor = AutoProcessor.from_pretrained("Xenova/yolos-small-300") # or hustvl/yolos-small-300
url = 'https://i.imgur.com/qOp3m0N.png' # very thin image

image = Image.open(requests.get(url, stream=True).raw).convert('RGB')
output = processor(image)
print(output['pixel_values'][0].shape)  # (3, 89, 1335)
```

A shape of (3, 89, 1335) is printed out, but this shouldn't be possible due to the `longest_edge` constraint in the [config.json](https://huggingface.co/Xenova/yolos-small-300/blob/main/preprocessor_config.json#L22):
```json
"size": {
  "longest_edge": 1333,
  "shortest_edge": 800
}
```

Here is the image used:
![image](https://github.com/huggingface/transformers/assets/26504141/74c75ab1-4678-4ff0-860b-b6b35a462eb8)


### Expected behavior

The image should have the maximum edge length be at most 1333 (1335 should not be possible)


## Task

Diagnose and fix the issue described above. The repository has been cloned at the relevant commit. Make the necessary code changes to resolve the bug.

## Success Criteria

Your code changes should resolve the described issue. The implementation will be verified against the expected patch using diff similarity scoring.

**Time Limit:** 30 minutes
