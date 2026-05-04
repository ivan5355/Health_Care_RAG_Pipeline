const SUGGESTIONS = [
  "What was the total billed amount?",
  "Which diagnosis codes were documented?",
  "What was the copay for the ECG?",
  "Who is the rendering provider?",
  "What is the patient's member ID?",
];

interface Props {
  onSelect: (question: string) => void;
}

export function SuggestedQuestions({ onSelect }: Props) {
  return (
    <div className="flex flex-col items-center gap-4 py-12">
      <h2 className="text-lg font-medium text-foreground">
        Ask a question about your healthcare documents
      </h2>
      <p className="text-sm text-muted-foreground">
        Try one of these questions or type your own
      </p>
      <div className="flex flex-wrap gap-2 justify-center max-w-lg">
        {SUGGESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => onSelect(q)}
            className="px-3 py-1.5 text-sm border rounded-full hover:bg-accent transition-colors"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
