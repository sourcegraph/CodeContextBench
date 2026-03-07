# IMPORTANT: Source Code Access

**Local source files are not present.** Your workspace does not contain source code. You **MUST** use Sourcegraph MCP tools to discover, read, and understand code before making any changes.

**Target Repositories (version-pinned mirrors):**

- `github.com/sg-evals/yt-dlp--39bc699d` — use `repo:^github.com/sg-evals/yt-dlp--39bc699d$` filter

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

# Fix: SWE-PolyBench__python__maintenance__bugfix__9ea927ce

**Repository:** github.com/sg-evals/yt-dlp--39bc699d (mirror of yt-dlp/yt-dlp)
**Language:** python
**Category:** contextbench_cross_validation

## Description

`--simulate` doesn't accurately simulate downloading under certain conditions
### DO NOT REMOVE OR SKIP THE ISSUE TEMPLATE

- [X] I understand that I will be **blocked** if I *intentionally* remove or skip any mandatory\* field

### Checklist

- [X] I'm reporting a bug unrelated to a specific site
- [X] I've verified that I have **updated yt-dlp to nightly or master** ([update instructions](https://github.com/yt-dlp/yt-dlp#update-channels))
- [X] I've checked that all provided URLs are playable in a browser with the same IP and same login details
- [X] I've checked that all URLs and arguments with special characters are [properly quoted or escaped](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#video-url-contains-an-ampersand--and-im-getting-some-strange-output-1-2839-or-v-is-not-recognized-as-an-internal-or-external-command)
- [X] I've searched [known issues](https://github.com/yt-dlp/yt-dlp/issues/3766) and the [bugtracker](https://github.com/yt-dlp/yt-dlp/issues?q=) for similar issues **including closed ones**. DO NOT post duplicates
- [X] I've read the [guidelines for opening an issue](https://github.com/yt-dlp/yt-dlp/blob/master/CONTRIBUTING.md#opening-an-issue)

### Provide a description that is worded well enough to be understood

When running a yt-dlp command with `--simulate` (and without an `-f` arg), the default format selection differs from an unsimulated run under any of these conditions:
- ffmpeg is not available
- the outtmpl is `-`
- the URL is for a livestream (and `--live-from-start` was not passed)

A dry-run/simulate option should actually simulate the behaviour that will occur when downloading.
This behaviour is currently undocumented. Either the behaviour should be changed or at the very least be documented.

---

*Copying initial discussion: https://github.com/yt-dlp/yt-dlp/pull/9805#discussion_r1588171627*

It looks like we can trace this logic back to https://github.com/ytdl-org/youtube-dl/commit/0017d9ad6de831384e74db14a821e4c94020c9ac

Back then, upstream's default format spec was only `best` if ffmpeg was not available. So a simulated run would result in a "requested formats not available" error if ffmpeg was not available and there was no combined video+audio format available. This `simulate` check seems to be added so that you could print json without having to manually pass `-f bv+ba` or `-f bv` etc in this scenario -- see the linked upstream PR



### Provide verbose output that clearly demonstrates the problem

- [X] Run **your** yt-dlp command with **-vU** flag added (`yt-dlp -vU <your command line>`)
- [ ] If using API, add `'verbose': True` to `YoutubeDL` params instead
- [X] Copy the WHOLE output (starting with `[debug] Command-line config`) and insert it below

### Complete Verbose Output

```shell
[debug] Command-line config: ['-vU', '--simulate', 'https://www.youtube.com/watch?v=2yJgwwDcgV8']
[debug] Encodings: locale cp1252, fs utf-8, pref cp1252, out utf-8, error utf-8, screen utf-8
[debug] yt-dlp version master@2024.04.28.221944 from yt-dlp/yt-dlp-master-builds [ac817bc83] (win_exe)
[debug] Python 3.8.10 (CPython AMD64 64bit) - Windows-10-10.0.22631-SP0 (OpenSSL 1.1.1k  25 Mar 2021)
[debug] exe versions: none
[debug] Optional libraries: Cryptodome-3.20.0, brotli-1.1.0, certifi-2024.02.02, curl_cffi-0.5.10, mutagen-1.47.0, requests-2.31.0, sqlite3-3.35.5, urllib3-2.2.1, websockets-12.0
[debug] Proxy map: {}
[debug] Request Handlers: urllib, requests, websockets, curl_cffi
[debug] Loaded 1810 extractors
[debug] Fetching release info: https://api.github.com/repos/yt-dlp/yt-dlp-master-builds/releases/latest
Latest version: master@2024.04.28.221944 from yt-dlp/yt-dlp-master-builds
yt-dlp is up to date (master@2024.04.28.221944 from yt-dlp/yt-dlp-master-builds)
[youtube] Extracting URL: https://www.youtube.com/watch?v=2yJgwwDcgV8
[youtube] 2yJgwwDcgV8: Downloading webpage
[youtube] 2yJgwwDcgV8: Downloading ios player API JSON
[youtube] 2yJgwwDcgV8: Downloading android player API JSON
WARNING: [youtube] Skipping player responses from android clients (got player responses for video "aQvGIIdgFDM" instead of "2yJgwwDcgV8")
[debug] Loading youtube-nsig.7d1f7724 from cache
[debug] [youtube] Decrypted nsig ZyUwo2vdMccktm7tN0 => ZvGvrjLHlKzcbw
[debug] Loading youtube-nsig.7d1f7724 from cache
[debug] [youtube] Decrypted nsig vYdxycJ0vBBgWEBA_9 => Etq9qDUH370hPg
[youtube] 2yJgwwDcgV8: Downloading m3u8 information
[debug] Sort order given by extractor: quality, res, fps, hdr:12, source, vcodec:vp9.2, channels, acodec, lang, proto
[debug] Formats sorted by: hasvid, ie_pref, quality, res, fps, hdr:12(7), source, vcodec:vp9.2(10), channels, acodec, lang, proto, size, br, asr, vext, aext, hasaud, id
[debug] Default format spec: bestvideo*+bestaudio/best
[info] 2yJgwwDcgV8: Downloading 1 format(s): 244+251
```



## Task

Diagnose and fix the issue described above. The repository has been cloned at the relevant commit. Make the necessary code changes to resolve the bug.

## Success Criteria

Your code changes should resolve the described issue. The implementation will be verified against the expected patch using diff similarity scoring.

**Time Limit:** 30 minutes
