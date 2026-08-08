import type { CoreFields, StatementDetail } from "./types";

export function formatDate(iso?: string | null): string {
  if (!iso) return "—";
  try {
    return new Intl.DateTimeFormat("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function languageLabel(code?: string): string {
  const map: Record<string, string> = {
    ur: "Urdu",
    pa: "Punjabi",
    ps: "Pashto",
    en: "English",
    urdu: "Urdu",
    punjabi: "Punjabi",
    pashto: "Pashto",
    english: "English",
  };
  if (!code) return "—";
  return map[code.toLowerCase()] || code;
}

export function scoreTone(score?: number | null): "good" | "warn" | "bad" | "neutral" {
  if (score == null) return "neutral";
  if (score >= 0.7) return "good";
  if (score >= 0.45) return "warn";
  return "bad";
}

export function asList(value?: string | string[] | null): string[] {
  if (!value) return [];
  if (Array.isArray(value)) return value.filter(Boolean);
  return [value];
}

export function getCoreFields(s: StatementDetail): CoreFields {
  const core = s.core_fields || {};
  return {
    time_of_incident: core.time_of_incident ?? s.time_of_incident,
    location: core.location ?? s.location,
    persons_present: core.persons_present ?? s.persons_present,
    sequence_of_events: core.sequence_of_events ?? s.sequence_of_events,
    relationship_to_parties: core.relationship_to_parties ?? s.relationship_to_parties,
  };
}

export function fieldLabel(field: string): string {
  const labels: Record<string, string> = {
    time_of_incident: "Time of incident",
    location: "Location",
    persons_present: "Persons present",
    sequence_of_events: "Sequence of events",
    relationship_to_parties: "Relationship",
    relationship: "Relationship",
  };
  return labels[field] || field.replace(/_/g, " ");
}
