/**
 * Client-side Uplift tool handlers → FastAPI /api/tools/*
 *
 * Per Uplift docs (assistants/tools): payload is
 *   JSON.parse(data.payload).arguments.raw_arguments
 * Handlers must register the same tool names as the assistant config
 * so the web WebRTC agent behaves like the phone agent.
 */

function apiBase(): string {
  const v = import.meta.env.VITE_API_URL;
  return typeof v === 'string' && v.length > 0 ? v : '';
}

/** Extract tool args from Uplift RPC payload shapes. */
export function extractToolArguments(payload: string): Record<string, unknown> {
  let parsed: Record<string, unknown> = {};
  try {
    parsed = JSON.parse(payload || '{}') as Record<string, unknown>;
  } catch {
    return {};
  }

  const argsBag = parsed.arguments;
  if (argsBag && typeof argsBag === 'object' && !Array.isArray(argsBag)) {
    const nested = argsBag as Record<string, unknown>;
    if (nested.raw_arguments && typeof nested.raw_arguments === 'object') {
      return nested.raw_arguments as Record<string, unknown>;
    }
    // Some SDKs put fields directly under arguments
    if (!('raw_arguments' in nested)) {
      return nested;
    }
  }

  if (parsed.raw_arguments && typeof parsed.raw_arguments === 'object') {
    return parsed.raw_arguments as Record<string, unknown>;
  }

  return parsed;
}

async function invokeTool(
  name: string,
  sessionId: string,
  data: { payload: string },
): Promise<string> {
  const arguments_ = extractToolArguments(data.payload);
  const res = await fetch(`${apiBase()}/api/tools/${name}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      roomName: sessionId,
      arguments: arguments_,
      raw_arguments: arguments_,
    }),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    return JSON.stringify({
      error: body.detail || res.statusText,
      presentationInstructions:
        'Mujhe khed hai, system mein masla aaya. Dobara koshish karein.',
    });
  }
  return JSON.stringify(body);
}

export type ToolEvent = { name: string; detail?: string; refCode?: string };

export function buildGawahTools(
  sessionId: string,
  onEvent?: (ev: ToolEvent) => void,
) {
  const wrap = (
    name: string,
    description: string,
    parameters: {
      type: 'object';
      properties: Record<string, unknown>;
      required: string[];
    },
    timeout = 15,
  ) => ({
    name,
    description,
    parameters,
    timeout,
    handler: async (data: { payload: string }) => {
      onEvent?.({ name, detail: 'invoked' });
      const raw = await invokeTool(name, sessionId, data);
      try {
        const parsed = JSON.parse(raw);
        const ref =
          parsed?.result?.refCode ||
          parsed?.result?.ref_code ||
          undefined;
        onEvent?.({
          name,
          detail: parsed?.presentationInstructions
            ? String(parsed.presentationInstructions).slice(0, 120)
            : parsed?.error
              ? `error: ${parsed.error}`
              : 'ok',
          refCode: ref,
        });
      } catch {
        onEvent?.({ name, detail: 'ok' });
      }
      return raw;
    },
  });

  // Schemas mirrored from gawah-backend/app/prompts/agent_config.py (GAWAH_TOOLS)
  return [
    wrap(
      'save_witness_statement',
      'Save the structured witness statement once all five fields have been collected. Call when you have enough information — do not wait for perfect answers.',
      {
        type: 'object',
        properties: {
          time_of_incident: {
            type: 'string',
            description: 'When the incident occurred. Accept approximate references.',
          },
          location: {
            type: 'string',
            description: 'Where the incident occurred.',
          },
          persons_present: {
            type: 'array',
            items: { type: 'string' },
            description: 'Names or descriptions of all persons present.',
          },
          sequence_of_events: {
            type: 'string',
            description: 'What happened, first-person narrative from the witness.',
          },
          relationship_to_accused: {
            type: 'string',
            description: 'How the witness knows the accused, if any.',
          },
          temporal_uncertainty: {
            type: 'boolean',
            description: 'True if approximate time references were used.',
          },
          language_of_call: {
            type: 'string',
            enum: ['ur', 'pa', 'ps', 'mixed'],
          },
          witness_type: {
            type: 'string',
            enum: ['eyewitness', 'hearsay', 'victim', 'unknown'],
          },
          corroboration_sources_mentioned: {
            type: 'array',
            items: { type: 'string' },
          },
          statement_delay_days: { type: 'number' },
          statement_delay_explanation: { type: 'string' },
        },
        required: ['sequence_of_events', 'location'],
      },
      20,
    ),
    wrap(
      'flag_inconsistency',
      'Silently flag an internal contradiction. Do not alert the witness.',
      {
        type: 'object',
        properties: {
          contradiction_description: { type: 'string' },
          segment_a: { type: 'string' },
          segment_b: { type: 'string' },
          contradiction_type: {
            type: 'string',
            enum: [
              'temporal',
              'spatial',
              'identity',
              'sequence',
              'sensory',
              'numerical',
            ],
          },
        },
        required: ['contradiction_description'],
      },
      8,
    ),
    wrap(
      'flag_intimidation',
      'Silently flag intimidation/threat/coercion signals. Escalates case.',
      {
        type: 'object',
        properties: {
          witness_statement: {
            type: 'string',
            description: 'Exact words that triggered the flag',
          },
        },
        required: ['witness_statement'],
      },
      8,
    ),
    wrap(
      'enable_privacy_mode',
      'Switch case to anonymous mode — no personal identity stored.',
      {
        type: 'object',
        properties: { reason: { type: 'string' } },
        required: [],
      },
      8,
    ),
    wrap(
      'assess_protection_need',
      'Assess witness protection eligibility when serious offence or intimidation is indicated.',
      {
        type: 'object',
        properties: {
          offence_type: {
            type: 'string',
            enum: [
              'terrorism',
              'sexual_offence',
              'murder',
              'kidnapping',
              'serious_assault',
              'other',
            ],
          },
          witness_is_victim: { type: 'boolean' },
          witness_appears_under_16: { type: 'boolean' },
          intimidation_already_flagged: { type: 'boolean' },
          province: {
            type: 'string',
            enum: [
              'Punjab',
              'Sindh',
              'Balochistan',
              'KPK',
              'Federal',
              'unknown',
            ],
          },
        },
        required: ['offence_type'],
      },
      12,
    ),
    wrap(
      'confirm_statement',
      "Record the witness's spoken confirmation after readback. Call when the witness says haan / yes.",
      {
        type: 'object',
        properties: {
          confirmed: {
            type: 'boolean',
            description: 'True when witness confirms the readback.',
          },
          ref_code: {
            type: 'string',
            description: 'Reference code just issued, if known.',
          },
        },
        required: [],
      },
      10,
    ),
  ];
}
