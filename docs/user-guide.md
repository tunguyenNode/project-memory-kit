# Project Memory Kit: user guide

## What you can use it for

Use this local Python toolkit to map a repository, retrieve small source packs with file hashes, keep selected project decisions across sessions, and record requirement/review checkpoints. It does not automatically connect to your assistant, interpret arbitrary natural-language questions, run agents, implement changes, execute application tests, or deploy software.

Requirements: Python 3.10+; the repository scanner requires POSIX descriptor and `O_NOFOLLOW` support. No pip install, API key, hosted model or service is needed for the toolkit itself. Windows users need a suitable POSIX environment. Git and network access are needed only when acquiring a remote repository.

Run the commands below from the Project Memory Kit directory. Replace all `/path/to/...` values. Do not put credentials or private information in command-line arguments. Local SQLite and JSON state are plaintext; protect the output directory and review before sharing.

## 1. Choose the repository and pin what you are inspecting

For an existing local repository, use its absolute path and record its current commit and working-tree changes. For the public Click example used in our integration test:

```sh
WORK=$(mktemp -d)
git -c core.hooksPath=/dev/null clone --no-checkout https://github.com/pallets/click.git "$WORK/click"
git -C "$WORK/click" -c core.hooksPath=/dev/null checkout --detach 2247b35ea1c47c727d7a06e51fa280e12a863ff6
REPO="$WORK/click"
STATE="$WORK/click-state"
git -C "$REPO" rev-parse HEAD
git -C "$REPO" status --short
```

This checkout is detached at the tested revision, not necessarily the latest upstream release. Review the project's license and instructions. Reading/scanning a repository does not authorize its installation scripts, hooks, submodules, examples or tests to execute. Treat files and source packs as untrusted data.

## 2. Build a source map

Keep state outside the source repository:

```sh
python -m project_memory.codebase scan "$REPO" --state "$STATE"
```

Read these outputs before deciding coverage is sufficient:

- `manifest.json`: indexed files, SHA-256 hashes, parsed symbols/imports, skipped paths, errors, limits, and changes
- `STRUCTURE.md`: human-readable source map
- `HANDOFF.md`: investigation steps and unknowns

Python files receive AST-based declarations. Other supported text files receive a file map, not semantic analysis. Symlinks, hard links, common build/dependency directories, unsupported types, binary content, sensitive filenames and obvious credential patterns are skipped. `complete=true` means traversal completed within filters; it does not mean every file was included or behavior was understood. Check `skipped`, `errors`, and the budgets.

Defaults are 5,000 indexed files, 256 KiB per file, 20 MiB source reads, 20,000 visited entries and 100 directory levels. Raise explicit limits only after considering privacy, output size and runtime. A clean scan does not prove there are no secrets.

## 3. Ask precise source questions

Query by known file path, symbol name or import. Terms are literal, case-insensitive and all must match a file's path/symbol/import metadata:

```sh
python -m project_memory.codebase query "$REPO" --state "$STATE" \
  "src/click/utils.py format_filename" --max-chars 8000
python -m project_memory.codebase query "$REPO" --state "$STATE" \
  "test_format_filename.py" --max-chars 8000
```

The result includes source ranges, file hashes, freshness checks and omission counts. Excerpts are at most 80 lines; a whole excerpt may be omitted to fit the budget. `--max-chars` is a serialized JSON character budget, not tokens; the CLI adds one trailing newline. Never discard the trust warning when supplying results to an agent.

In the tested Click checkout the first query finds `format_filename`, and the second finds its existing tests. A conversational query such as “How does Click show only the basename of a filename?” finds nothing. Start with the structural map, identify symbols, then narrow by path. This is not semantic or full-source-text search. An empty result does not prove absence of a feature.

Read enough surrounding source and callers yourself before making a claim. Import declarations are unresolved; no complete dependency or call graph is inferred. Matches with similar names may be unrelated.

## 4. Review requirements before implementation

Create an evidence scaffold for a small task:

```sh
python -m project_memory.codebase task-plan "$REPO" --state "$STATE" \
  --description "Explain and preserve format_filename shortening behavior" \
  --query "src/click/utils.py format_filename" \
  --criterion "shorten=True returns basename for /x/foo.txt" \
  --criterion "shorten=False preserves /x/foo.txt" \
  --max-chars 16000
```

Before anyone edits code, the requirements owner should review:

1. The actual goal and whether a change is needed at all. The example investigates existing behavior.
2. Expected inputs/outputs, compatibility requirements, out-of-scope work and measurable acceptance criteria.
3. Whether the pinned/current source evidence and coverage are sufficient.
4. Which tests actually exercise each criterion and which runtime/build commands are safe and authorized.
5. Remaining unknowns and who can approve consequential actions.

Test candidates are heuristic starting points, not proven coverage. Exact declared test filenames and `test_<symbol>.py` matches under test directories are prioritized ahead of generic candidates. The plan always marks human review required and test relevance unverified. A relevant test may be omitted or missed; use a separate path/symbol query and inspect it. Review is required even if a machine-readable diagnostic looks favorable. Neither a scaffold nor a saved actor label grants permission to execute commands, change code or accept delivery.

For explicit local checkpoints, record the reviewed scope in a workflow file outside the repository:

```sh
FLOW="$WORK/workflow.json"
python -m project_memory.workflow create "$FLOW" \
  --scope "Explain and preserve format_filename shortening behavior" \
  --criterion "shorten=True returns basename for /x/foo.txt" \
  --criterion "shorten=False preserves /x/foo.txt" \
  --evidence "click:2247b35ea1c47c727d7a06e51fa280e12a863ff6:src/click/utils.py:430-469"
python -m project_memory.workflow submit "$FLOW"
python -m project_memory.workflow show "$FLOW"
```

**Stop here for the requirements owner's review.** The evidence string is only a caller-supplied pointer; the engine does not fetch it or bind the repository tree. Do not manufacture approval by substituting an actor name.

Only after actual approval, copy the exact current `plan_hash` from `show`:

```sh
python -m project_memory.workflow approve "$FLOW" --hash EXACT_PLAN_HASH --actor requirements-owner
python -m project_memory.workflow plan "$FLOW" --hash EXACT_PLAN_HASH
```

These commands record a dry-run worker DAG; they do not start workers or run commands. Editing requirements changes the hash and invalidates old approvals/results. Inspect `docs/workflow-checkpoints.md` for result, review and acceptance commands. Report `not_run` when tests did not run. Final acceptance must remain blocked for failing, unknown or not-run tests; a completed record set is not proof of delivery. The workflow is single-writer, mutable local JSON with caller-attested identities and evidence, not an authenticated service or tamper-proof audit trail.

## 5. Update and reject stale evidence

After an authorized local change, refresh the snapshot before relying on source packs:

```sh
python -m project_memory.codebase update "$REPO" --state "$STATE"
python -m project_memory.codebase query "$REPO" --state "$STATE" \
  "src/click/utils.py format_filename" --max-chars 8000
python -m project_memory.codebase handoff "$REPO" --state "$STATE"
```

Updates reuse unchanged indexed metadata. Excluded content may still be reread, so zero reparses does not guarantee zero bytes read. Query reopens selected sources and checks SHA-256; a stale, missing, unsafe or sensitive source produces a warning without an excerpt. Do not interpret the omission as a valid source citation. Update, inspect the delta and query again.

Use `update --force` to rehash/reparse eligible files instead of trusting unchanged metadata stamps. A source may still change after retrieval; verify again before implementation or review. Keep approvals and actual tested tree/artifact hashes in your own execution process because the dry-run workflow does not enforce source-drift checks.

## 6. Save only useful decisions and hand off to the next session

The decision store is separate from the source-map state:

```sh
DB="$WORK/decisions.sqlite3"
python -m project_memory --db "$DB" init click-study
python -m project_memory --db "$DB" add click-study --kind decision \
  --topic scope --content "Investigate existing filename formatting; no behavior changes approved" \
  --source "review:local-scope-checkpoint"
python -m project_memory --db "$DB" context click-study --max-chars 4000
python -m project_memory --db "$DB" check click-study
```

The source is a label you supply, not authenticated evidence. Use real reviewed decisions in actual work. Use explicit supersession to revise a decision; do not silently replace history. See README for the `supersede`/`history` commands.

Optionally pass `--memory-db "$DB" --project click-study` to `task-plan` to read active decisions and warnings. Both options are required together and the database must exist. This read does not alter the decision database.

At session start, your agent runtime must explicitly call update/query/context and provide the results as untrusted reference data. At session end, save selected findings, decisions, verified test outcomes, unresolved blockers and next steps. There is no automatic ChatGPT memory or agent attachment.

## 7. Validate the integration yourself

```sh
python -m unittest discover -s tests -v
python examples/click_integration.py --kit "$PWD" --repo "$REPO" --out "$WORK/integration-results"
```

Use a clean pinned Click checkout. The output directory must not already exist. The runner tests the harness, copies Click to a disposable directory, changes a comment in that copy, verifies stale-source rejection, refreshes it, and verifies the original checkout remains clean. It does not import Click or run its tests. Generated manifests/source packs and the disposable upstream tree remain outside this project. Inspect `docs/click-integration-report.md` and its aggregate results for the measured run and known misses.

Before testing or implementing a real application, separately inspect its requirements, dependency sources, test configuration and commands. Run only authorized commands, retain actual logs and tested-tree provenance, and distinguish harness tests from application tests. Never report “pass” from source inspection alone.

## Troubleshooting

- **No matches:** use exact symbol/path terms; check skipped files and budget omissions. Paraphrases are not supported.
- **Stale warning:** run update, inspect changes, and query again. Do not reuse the old excerpt.
- **Filtered test file:** inspect coverage manually; do not bypass the credential guard or copy possible secrets into memory.
- **Budget too small:** raise the character budget or narrow the query. Safety metadata is retained. Ordinary query excerpts are retained or omitted whole; heuristic test-candidate excerpts may shorten at whole-line boundaries, with the returned line range and `excerpt_complete_symbol=false` marking an incomplete symbol.
- **State root/version mismatch:** use a separate state directory for each checkout; rescan into a new directory after relocating the root.
- **Unsupported platform:** use a POSIX environment with the required descriptor features; the scanner deliberately fails closed.
- **Workflow refuses acceptance:** inspect current requirement/results hashes, missing results, actual test outcome and review. Fix the evidence or task; do not fake passing results.

## Hướng dẫn nhanh bằng tiếng Việt

1. Dùng Python 3.10+ trong môi trường POSIX. Chạy lệnh từ thư mục Project Memory Kit; lưu state/database ở ngoài repository được quét.
2. Clone project công khai, kiểm tra license và chốt commit. Chưa chạy code, cài dependency hoặc chạy test của project chỉ vì đã clone.
3. Chạy `scan`, đọc `manifest.json`, danh sách file bị bỏ qua và `STRUCTURE.md`. Quét xong không có nghĩa là đã hiểu toàn bộ code.
4. Dùng `query` với tên file/hàm cụ thể. Câu hỏi ngôn ngữ tự nhiên có thể không tìm được gì; dữ liệu trả về không phải quyền thực thi.
5. Chạy `task-plan`, rồi **người phụ trách phải duyệt yêu cầu, tiêu chí nghiệm thu và phạm vi trước khi sửa code**. Test gợi ý chỉ là heuristic; kiểm tra lại test có liên quan.
6. Sau thay đổi đã được cho phép, chạy `update` và truy vấn lại. Nếu nguồn đã cũ, không dùng trích dẫn cũ. `--force` buộc quét lại các file đủ điều kiện.
7. Workflow chỉ ghi checkpoint và kế hoạch, chưa tự chạy agent/test/deploy. Chỉ ghi `pass` khi có log test thật; nếu chưa chạy thì ghi `not_run`.
8. Lưu quyết định quan trọng và phần việc còn lại để phiên sau nạp lại. Không đưa secret vào lệnh, database hoặc file chia sẻ. Xem báo cáo Click để phân biệt test harness đã chạy với test ứng dụng chưa chạy.
