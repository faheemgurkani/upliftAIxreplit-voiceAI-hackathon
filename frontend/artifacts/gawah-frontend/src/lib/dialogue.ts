export type DialogueRole = 'agent' | 'witness';

export interface DialogueTurn {
  role: DialogueRole;
  text: string;
  id: string;
  at?: number;
}

/** Build Agent/Witness chat lines for storage + display */
export function formatDialogueTranscript(turns: DialogueTurn[]): string {
  return turns
    .filter((t) => t.text.trim())
    .map((t) => `${t.role === 'agent' ? 'ایجنٹ' : 'گواہ'}: ${t.text.trim()}`)
    .join('\n\n');
}

export function witnessOnlyText(turns: DialogueTurn[]): string {
  return turns
    .filter((t) => t.role === 'witness' && t.text.trim())
    .map((t) => t.text.trim())
    .join(' ');
}
