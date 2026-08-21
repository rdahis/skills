# Markup mode

Suggestions written into the file itself, for edits too large to type into the
browser. They are not Overleaf tracked changes — they are visible, compilable,
reversible markup that a co-author reads in the PDF and resolves with one
command.

Use it for a new section, a long table, an appendix, a rewritten subsection.
Use `suggest` mode for anything a person could reasonably type by hand.

## Preamble

Check what the project already loads before adding anything. Most LaTeX papers
already have `xcolor`; many have `ulem`.

**Option A — the `changes` package** (available on Overleaf, gives
`\listofchanges`):

```latex
\usepackage[markup=underlined]{changes}
```

**Option B — dependency-light, if the project already loads `xcolor` and
`ulem`:**

```latex
% --- suggestion markup (temporary; delete this block once resolved) ---
\providecommand{\added}[1]{\textcolor{blue}{#1}}
\providecommand{\deleted}[1]{\textcolor{red}{\sout{#1}}}
\providecommand{\replaced}[2]{\added{#1}\deleted{#2}}
```

`\providecommand` will not clobber an existing definition, so Option B is safe
to drop into a project that already defines any of the three.

Say which option you are adding and why, and put the block where the project
keeps its other macro definitions. If the project has a shared `preamble.tex`
included by several documents, add it there once, not per file.

## Inline form

For edits inside a paragraph:

```latex
The estimated premium is \replaced{12.4}{11.8} percent.
Coverage is \added{materially }better after the second linking pass.
\deleted{This sentence overstates the causal claim.}
```

Argument order for `\replaced` is `{new}{old}` — the `changes` package
convention. Getting it backwards silently inverts every suggestion, so check it.

Rules:

- **Never nest** markup macros inside each other.
- **Never wrap a block environment** in a macro argument. `\added{\begin{table}
  … \end{table}}` breaks, as does anything containing `verbatim`, `lstlisting`,
  or a `&`-heavy `tabular`. Use the block form for those.
- Keep each macro on one logical unit — a phrase, a clause, a sentence. A
  macro spanning three paragraphs is unreadable in the PDF and painful to
  reject.
- Do not put a `%` comment inside a macro argument.

## Block form

For anything structural, sentinel comments instead of macros:

```latex
%% >>> SUGGEST ADD referee-2-robustness >>>
\subsection{Sensitivity to the trimming threshold}
\input{tables/sensitivity}
%% <<< SUGGEST END <<<
```

For a proposed deletion, comment each line with a single leading `%` at column
zero, so the removal is exactly reversible:

```latex
%% >>> SUGGEST DEL overstated-causal-claim >>>
%\begin{table}[htbp]
%  \caption{Naive OLS estimates}
%  \input{tables/naive_ols}
%\end{table}
%% <<< SUGGEST END <<<
```

The label after `ADD` or `DEL` is free text — use the referee comment, ticket,
or a short slug. It shows up in `--list` output and makes selective resolution
possible.

Exact tokens, matched case-sensitively by the resolver:

```
%% >>> SUGGEST ADD <label> >>>
%% >>> SUGGEST DEL <label> >>>
%% <<< SUGGEST END <<<
```

Blocks do not nest.

## Resolving

```bash
python3 scripts/resolve-markup.py paper/main.tex --list
python3 scripts/resolve-markup.py paper/main.tex --accept
python3 scripts/resolve-markup.py paper/main.tex --reject
python3 scripts/resolve-markup.py paper/sections/*.tex --accept --label referee-2-robustness
```

| Construct | `--accept` | `--reject` |
|---|---|---|
| `\added{X}` | `X` | removed |
| `\deleted{X}` | removed | `X` |
| `\replaced{new}{old}` | `new` | `old` |
| `\highlight{X}` | `X` | `X` |
| `SUGGEST ADD` block | body kept, sentinels dropped | block removed |
| `SUGGEST DEL` block | block removed | body uncommented |

The resolver writes a `.bak` next to each file it changes, skips macros that
appear inside a LaTeX comment, and refuses to run on a file with an unbalanced
or unterminated construct rather than guessing.

Resolution edits files, so it belongs to the mirror path: run the freshness
protocol first, then resolve, then round-trip and verify. Delete the temporary
preamble block once no markup remains.

## When the project has no mirror

Type the markup into the browser instead. Block form is easier to type than
nested macros, and — unlike native tracked changes — needs no premium plan. It
is the free-plan route to reviewable suggestions.

## Whole-draft comparison

For "show me everything that changed since the version they reviewed",
markup is the wrong tool. Compile the two versions from the mirror and diff
them:

```bash
latexdiff old/main.tex new/main.tex > diff.tex
```

Compile `diff.tex` locally and give the user the PDF. Do not upload the diff
into the Overleaf project — it is a throwaway artifact and adds a file the
co-authors did not ask for.
