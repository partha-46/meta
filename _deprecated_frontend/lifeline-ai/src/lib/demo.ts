export const DEMO_CASES = [
  {
    id: "demo_cardiac",
    title: "Emergency cardiac case",
    symptoms: "I have chest pain and shortness of breath. The pain is radiating to my left arm.",
    location: "Westside",
  },
  {
    id: "demo_fever",
    title: "Fever & sore throat",
    symptoms: "I have fever and sore throat for the last 2 days.",
    location: "Downtown",
  },
  {
    id: "demo_collapse",
    title: "Unresponsive collapse",
    symptoms: "Person collapsed and is unresponsive. Blue lips and very slow breathing.",
    location: "Northside",
  },
] as const;

export function urgencyMeta(urgency: "low" | "medium" | "high" | "emergency") {
  switch (urgency) {
    case "emergency":
      return { label: "Emergency", pill: "bg-red-600 text-white", border: "border-red-200" };
    case "high":
      return { label: "High", pill: "bg-orange-500 text-white", border: "border-orange-200" };
    case "medium":
      return { label: "Medium", pill: "bg-blue-600 text-white", border: "border-blue-200" };
    default:
      return { label: "Low", pill: "bg-emerald-600 text-white", border: "border-emerald-200" };
  }
}

