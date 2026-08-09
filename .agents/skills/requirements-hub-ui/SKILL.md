---
name: requirements-hub-ui
description: Design system et règles de composants React/Tailwind pour RequirementsHubSegula (Dual-Persona UI Stripe vs Linear style).
---

# Skill UI/UX RequirementsHubSegula

Ce skill fournit les composants de référence et les tokens CSS validés pour l'application `RequirementsHubSegula`, en respectant la séparation stricte des deux personas : **Utilisateur Métier (Stripe Style)** et **Ingénieur IA (Linear Style)**.

---

## 1. Tokens CSS (CSS Variables)

Ajouter dans le fichier `frontend/src/shared/styles/variables.css` :

```css
@import "tailwindcss";

:root {
  /* Portail Métier - Warm Scandinavian (Stripe Style) */
  --portal-bg: #FBF9F5;
  --portal-card: #FFFFFF;
  --portal-border: #E5E2DC;
  --portal-text-main: #1C1917;
  --portal-text-muted: #78716C;
  --portal-accent: #2D6A4F;

  /* Dashboard Admin - Obsidian Gold (Linear Style) */
  --admin-bg: #09090B;
  --admin-card: #121215;
  --admin-border: rgba(255, 255, 255, 0.1);
  --admin-text-main: #FAFAFA;
  --admin-text-muted: #71717A;
  --admin-accent: #D4AF37;
  --admin-go: #10B981;
  --admin-nogo: #EF4444;
  --admin-clarify: #F59E0B;
}
```

---

## 2. Composants de Référence

### A. Portail Métier (`/portal`) : Wizard Card (Stripe / Progressive Disclosure)

```tsx
// frontend/src/portal/components/WizardStepCard.jsx
import React from 'react';

export function WizardStepCard({ stepNumber, totalSteps, title, description, children }) {
  return (
    <div className="max-w-2xl mx-auto bg-white border border-[#E5E2DC] rounded-2xl p-8 shadow-[0_4px_20px_rgba(0,0,0,0.03)] transition-all duration-300">
      <div className="flex items-center justify-between border-b border-[#E5E2DC] pb-4 mb-6">
        <span className="text-xs font-semibold uppercase tracking-wider text-[#78716C]">
          Étape {stepNumber} sur {totalSteps}
        </span>
        <div className="flex gap-1.5">
          {Array.from({ length: totalSteps }).map((_, i) => (
            <div
              key={i}
              className={`h-1.5 rounded-full transition-all duration-300 ${
                i + 1 === stepNumber ? 'w-6 bg-[#1C1917]' : 'w-1.5 bg-[#E5E2DC]'
              }`}
            />
          ))}
        </div>
      </div>
      <h2 className="text-2xl font-serif text-[#1C1917] tracking-tight">{title}</h2>
      <p className="text-sm text-[#78716C] mt-1 mb-6">{description}</p>
      {children}
    </div>
  );
}
```

### B. Dashboard Ingénieur IA (`/admin`) : Table Row & Status Pill (Linear Style)

```tsx
// frontend/src/admin/components/SubmissionRow.jsx
import React from 'react';

const STATUS_CONFIG = {
  GO: { label: 'GO', bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20' },
  NO_GO: { label: 'NO GO', bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/20' },
  NEEDS_CLARIFICATION: { label: 'CLARIFICATION', bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20' },
  PENDING: { label: 'EN ATTENTE', bg: 'bg-zinc-500/10', text: 'text-zinc-400', border: 'border-zinc-500/20' },
};

export function SubmissionRow({ item, onSelect }) {
  const status = STATUS_CONFIG[item.status] || STATUS_CONFIG.PENDING;

  return (
    <tr 
      onClick={() => onSelect(item.request_id)}
      className="border-b border-white/5 bg-[#121215] hover:bg-white/[0.03] transition-colors cursor-pointer group text-sm"
    >
      <td className="py-3 px-4 text-zinc-400 font-mono text-xs">{item.request_id.slice(0, 8)}...</td>
      <td className="py-3 px-4 font-medium text-zinc-200 group-hover:text-amber-400 transition-colors">
        {item.title}
      </td>
      <td className="py-3 px-4 text-zinc-400">{item.department}</td>
      <td className="py-3 px-4">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${status.bg} ${status.text} ${status.border}`}>
          {status.label}
        </span>
      </td>
      <td className="py-3 px-4 font-mono font-semibold text-zinc-200">
        {item.score !== undefined ? `${(item.score * 100).toFixed(0)}%` : '—'}
      </td>
      <td className="py-3 px-4 text-right">
        <button className="text-xs text-zinc-400 hover:text-amber-400 px-3 py-1 rounded bg-white/5 hover:bg-white/10 transition-all">
          Revoir →
        </button>
      </td>
    </tr>
  );
}
```
