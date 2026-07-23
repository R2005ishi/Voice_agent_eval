# Voice Agent Failure Taxonomy Report

Automated adversarial testing results for the toy scheduling agent.

## Summary

| Category | Total Tests | Failures | Failure Rate |
|---|---|---|---|
| ambiguity/topic_switch | 6 | 2 | 33% |
| ambiguity/vague_reference | 5 | 3 | 60% |
| asr_error/combined | 12 | 7 | 58% |
| asr_error/filler_injection | 12 | 2 | 17% |
| interruption/barge_in_correction | 4 | 3 | 75% |

## Example Failures

### ambiguity/topic_switch

**Test ID:** `f3f50d8e`

```
CALLER: Hello, I need to schedule a cleaning
AGENT: What date would you like for your appointment?
CALLER: Can you also tell me how often the copays are for new patients?
AGENT: I'd be happy to help with that later. Can you please confirm your preferred date for the cleaning appointment?
```
**Judge findings:**
- `task_coherence`: FAIL — The assistant took an action (booking) based on a guess rather than confirmed info
- `no_repetition_loop`: FAIL — The assistant re-asked for information (preferred date) that was already provided earlier in the transcript

**Test ID:** `gemini_mobile_02fa6f`

```
CALLER: Hi Gemini, I need to book a dental appointment for next Tuesday at 2 PM.
AGENT: I can help you arrange that. While I'm setting this up, could you tell me the name of the dental practice so I have all the correct-
CALLER: Wait Gemini, before that, what are your clinic copays for new patients?
AGENT: To give you an accurate copay amount, could you tell me the name of the dental clinic you're planning to visit?
```
**Judge findings:**
- `task_coherence`: FAIL — The assistant took an action (booking) based on a guess rather than confirmed info about copays.
- `no_repetition_loop`: FAIL — The assistant re-asked for information (clinic name) that was already provided earlier in the transcript.

### ambiguity/vague_reference

**Test ID:** `92069dc7`

```
CALLER: Hi, I'd like to book an appointment
AGENT: What type of appointment would you like to schedule?
CALLER: Can I book a time slot for my cleaning?
AGENT: Do you have a preferred date in mind for your cleaning appointment?
```
**Judge findings:**
- `task_coherence`: FAIL — The assistant took an action (booking) based on a guess rather than confirmed info
- `no_repetition_loop`: FAIL — The assistant re-asked for information (preferred date) that was already provided earlier in the transcript

**Test ID:** `a9a9fc6f`

```
CALLER: Hello, I need to schedule a cleaning
AGENT: What date would you like to schedule your appointment?
CALLER: Can we squeeze this in on Tuesday?
AGENT: Do you have a preferred time slot for Tuesday, such as morning or afternoon?
```
**Judge findings:**
- `task_coherence`: FAIL — The assistant assumed the caller wanted a specific time slot on Tuesday, but the original request was to 'squeeze' the appointment in on that day.
- `no_repetition_loop`: FAIL — The assistant re-asked for information about time slots, which was already provided earlier in the conversation.

### asr_error/combined

**Test ID:** `56896cb2`

```
CALLER: Hi, I'd like to book an appointment
AGENT: What type of appointment are you looking to schedule?
CALLER: My name is
AGENT: I didn't quite catch that. Can you please repeat your full name for me?
```
**Judge findings:**
- `task_coherence`: FAIL — The assistant took an action (booking) based on a guess rather than confirmed info
- `no_repetition_loop`: FAIL — The assistant re-asked for information (full name) that was already provided earlier in the transcript

**Test ID:** `97c74e64`

```
CALLER: Hi, I'd like to book an appointment
AGENT: What type of appointment would you like to schedule?
CALLER: I'd like a
AGENT: Can you please clarify what "a" refers to in this case? Are you referring to the type of appointment or something else?
```
**Judge findings:**
- `no_repetition_loop`: FAIL — Assistant re-asked for information (type of appointment) that was already provided earlier in the transcript.

### asr_error/filler_injection

**Test ID:** `0533f5e5`

```
CALLER: Hi, I'd like to book an appointment
AGENT: What type of appointment would you like to schedule?
CALLER: My [background noise] name is Sarah Johnson
AGENT: Can you please speak more clearly? I didn't quite catch your name.
```
**Judge findings:**
- `task_coherence`: FAIL — The assistant took an action (asking for name) based on unconfirmed information.
- `no_repetition_loop`: FAIL — The assistant re-asked for information (name) that was already provided earlier in the transcript.

**Test ID:** `d176d0d9`

```
CALLER: Hello, I need to schedule a cleaning
AGENT: What date would you like for your appointment?
CALLER: My [background noise] name is Sarah Johnson
AGENT: Can you please speak up so I can hear your name clearly?

(And just to confirm, you'd like a cleaning appointment with us?)
```
**Judge findings:**
- `task_coherence`: FAIL — Assistant took an action (booking) based on a guess rather than confirmed info
- `no_repetition_loop`: FAIL — Assistant re-asked for information (name) that was already provided earlier in the transcript

### interruption/barge_in_correction

**Test ID:** `bde08f2d`

```
CALLER: Hi, I'd like to book an appointment
AGENT: What type
CALLER: Wait, no, actually, actually book it for my son not me
AGENT: Can you please tell me your son's name?
```
**Judge findings:**
- `task_coherence`: FAIL — Assistant booked an appointment for the caller's son despite the caller explicitly stating they wanted to book an appointment for themselves.
- `context_recovery`: FAIL — Assistant failed to acknowledge and track state changes in the conversation, switching from booking an appointment for the caller to booking one for their son.

**Test ID:** `088504f6`

```
CALLER: Hi, I'd like to book an appointment
AGENT: What type
CALLER: Wait, no, actually, actually book it for my son not me
AGENT: Can you please tell me your son's name?
```
**Judge findings:**
- `task_coherence`: FAIL — Assistant booked an appointment for the caller's son despite the caller explicitly stating they wanted to book an appointment for themselves.
- `context_recovery`: FAIL — Assistant failed to acknowledge and track state changes in the conversation, switching from booking an appointment for the caller to booking one for their son.
