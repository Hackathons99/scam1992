# Project Challenges and Ambiguities

_Documenting architectural hurdles and interpretation gaps encountered during implementation._

## 1. API Response Structure Conflict

**The Problem:**
The initial understanding of the API required a rich response structure including `scamDetected` flags, `engagementMetrics`, and `extractedIntelligence` in every synchronous HTTP response.
However, **docs/ORIGINALDOC.TXT (Section 8)** explicitly dictates a simplified structure:

```json
{
  "status": "success",
  "reply": "Agent message here"
}
```

**The Ambiguity:**
It was unclear whether the platform expected the "rich" data in the API response OR the Callback.
**Our Resolution:**
We strictly adhered to Section 8 for the synchronous API (returning only `reply`) and moved all rich data reporting to the mandatory Callback (Section 12).

## 2. Callback Timing: "Final Result" vs. "Real-Time"

**The Problem:**
Section 12 states the callback must be sent "Only after intelligence extraction is **finished**" and treated as the "Final Step".
In a real-time conversational API, there is no definitive "End" signal. The scammer could provide a Bank Account in message 5 and a UPI ID in message 10.
**The Ambiguity:**
If we send the callback at message 5 (when we first detect scam + confirmed intel), are we allowed to send it _again_ at message 10? The doc implies a "One-Shot" final report.
**Our Resolution:**
We implemented a **Rolling Update** strategy. We trigger the callback as soon as significant intel (Bank/UPI/Phone/Link) is found. We removed the "lock" that prevented subsequent callbacks, ensuring that if better intel is found later, the platform receives the most complete dataset, effectively treating the latest callback as the "Final" one.

## 3. "Scam Score" Definition

**The Problem:**
The document mentions `scamDetected` (Boolean) and a `scam_score` (0-100) implicitly in examples, but provides no rubric or algorithm for calculating it.
**The Ambiguity:**
Is a "Scam" defined by keywords? By intent? By AI confidence? There is no standardized threshold provided (e.g., is 60 a scam? or 90?).
**Our Resolution:**
We implemented an internal heuristic:

- **Threshold:** > 60
- **Logic:** The LLM evaluates the conversation context. If the score exceeds 60, we flip `scamDetected = True`.

## 4. Definition of "Significant Intel"

**The Problem:**
The document requires a callback when "Intelligence extraction is finished".
**The Ambiguity:**
Does finding just a "Suspicious Keyword" count as "Intel"? If we trigger on keywords, we might spam the endpoint. If we wait for a Bank Account, we might never trigger if the scammer is cautious.
**Our Resolution:**
We defined "Trigger-Worthy Intel" as:

- **Bank Account Numbers** OR
- **UPI IDs** OR
- **Phone Numbers** OR
- **Phishing Links**
  We do _not_ trigger the callback solely on "Suspicious Keywords" to avoid false positives or low-value reports.

## 5. Callback Payload Redundancy

**The Problem:**
The Callback payload (Section 12) repeats `totalMessagesExchanged` and `sessionId`, which are also implicitly tracked by the platform's API state.
**The Ambiguity:**
It's unclear why the platform can't link the session internally.
**Our Resolution:**
We strictly followed the schema, calculating `totalMessagesExchanged` manually in our `session_intel_store` and including it in every payload.
