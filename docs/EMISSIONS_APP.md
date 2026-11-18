# Emissions Test Insights

Emissions Test Insights is a local retrieval-augmented generation (RAG) chat
application for exploring illustrative engine and catalyst test reports. It
provides both a Streamlit web interface and a terminal interface.

## Purpose

The application lets users ask questions about:

- Engine-out carbon monoxide, hydrocarbons, nitrogen oxides, and carbon dioxide
- Catalyst conversion efficiency
- Test setup, operating conditions, and sampling methods
- Differences between available reports
- The limitations of the reported measurements

The agent is grounded in local text reports and is instructed to cite the exact
source filename for factual claims.

> [!IMPORTANT]
> All records in `data/emissions_tests/` are synthetic examples. They are not
> certified measurements, real-world test results, regulatory advice, or
> evidence of compliance.

## Architecture

The application has four main components:

1. **User interface**
   - `emissions_app.py` provides the Streamlit chat and report sidebar.
   - `emissions_main.py` provides an interactive terminal chat.
2. **Agent**
   - `agents/emissions_agent.py` creates the Anthropic chat model and LangChain
     agent.
   - It supplies the `search_emissions_reports` tool and conversation memory.
3. **Retrieval**
   - `agents/emissions_retrieval.py` loads and searches the local reports.
   - It uses BM25 lexical ranking over paragraph-sized chunks.
4. **Data**
   - `data/emissions_tests/*.txt` contains the illustrative reports.

### Request flow

1. A user submits a question in Streamlit or the terminal.
2. The agent decides whether local report evidence is required.
3. When appropriate, it invokes `search_emissions_reports`.
4. The retrieval module:
   - reads every `.txt` file in the emissions data directory,
   - splits each report into paragraphs,
   - tokenizes the report title and paragraphs,
   - ranks the paragraphs with BM25,
   - returns up to five matching paragraphs with source filenames.
5. The model produces an answer from the retrieved evidence.
6. The interface displays the answer and preserves conversation state.

Streamlit uses a unique thread ID and an in-memory LangGraph checkpointer for
the current session. The terminal implementation uses the fixed thread ID
`emissions-cli`. Starting a new Streamlit conversation creates a new thread ID.

## Prerequisites

- Python 3.10 or newer
- An Anthropic API key
- The dependencies listed in `requirements.txt`

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Create a `.env` file in the project root:

```text
ANTHROPIC_API_KEY=your-anthropic-api-key
```

The application loads this value with `python-dotenv`.

## Run the applications

### Streamlit web app

```powershell
streamlit run emissions_app.py
```

Open the local URL printed by Streamlit. The sidebar shows the number of
available reports and their filenames.

Use the **New conversation** button to reset the chat history and create a fresh
conversation thread.

### Terminal app

```powershell
python emissions_main.py
```

Enter a question at the prompt. Use `quit` or `exit` to end the chat.

## Example questions

- "Compare the CO and NOx results in the catalyst reports."
- "What operating conditions were used in ENG-101?"
- "What is the THC conversion at 500 deg C?"
- "Can CAT-201 be used to infer cold-start catalyst performance?"
- "Which report provides the engine-out carbon dioxide result?"

The answer may include a source citation such as `[CAT-201.txt]`. If the reports
do not contain enough evidence, the agent should say so rather than infer a
result.

## Report format

Reports are UTF-8 text files in `data/emissions_tests/`. The retrieval module
expects a title followed by blank-line-separated paragraphs:

```text
Title: Example report title
Record type: Illustrative synthetic report
Test date: 2025-01-01

Test setup: Operating conditions and equipment details.

Measured results: Results and units.

Interpretation: Context and known limitations.
```

The first paragraph is used as the report title. Its `Title:` prefix is removed
before indexing. Every subsequent paragraph is indexed separately while retaining
the source filename.

To add a report, place a `.txt` file in `data/emissions_tests/` and follow this
format. Restart the app to ensure the latest files are discovered.

## Retrieval behavior

Retrieval is lexical rather than semantic:

- Matching is based on exact normalized words.
- Common punctuation is removed.
- Words are converted to lowercase.
- The highest-ranking paragraph matches are selected with BM25.
- Results are limited to five matches.
- A query with no matching terms produces a no-evidence response.

The report title is included in each chunk's text for matching. The formatted
result includes the exact source filename, report title, and evidence paragraph.

## Configuration and errors

### Missing API key

If `ANTHROPIC_API_KEY` is not set, agent creation raises:

```text
Missing API key: ANTHROPIC_API_KEY. Add it to your .env file.
```

The Streamlit app displays this error and stops initialization.

### Retrieval failures

Retrieval runs locally and does not require a retrieval API key. If no report
matches the question, the agent receives an explicit no-evidence message.

### Model connection failures

The Streamlit interface displays a general answer-generation error. The terminal
interface allows the exception to propagate to the process.

## Safety and interpretation

The system prompt requires the model to:

- retrieve evidence before answering test-finding questions,
- cite exact source filenames,
- distinguish measurements from interpretation,
- compare only like-for-like conditions and units,
- state when evidence is insufficient,
- avoid presenting the synthetic records as real or certified data.

Answers should still be reviewed before use. The application does not perform
independent unit validation, compliance calculations, or verification of source
data.

## Troubleshooting

### No reports appear in the sidebar

Confirm that `.txt` reports exist in `data/emissions_tests/` and restart
Streamlit.

### Streamlit cannot create the agent

Check that `ANTHROPIC_API_KEY` is present in the project-root `.env` file and
that the virtual environment has the required dependencies installed.

### The agent gives an unrelated answer

Try including report-specific names or technical terms, such as `CAT-201`,
`NOx`, `500 deg C`, or `ENG-101`. Lexical retrieval may not recognize semantic
paraphrases without shared terms.
