# RULES DE DESIGN UI/UX SPÉCIFIQUES À REQUIREMENTSHUB SEGULA

## 🎯 ARCHITECTURE UI DUAL-PERSONA (OBLIGATOIRE)

L'application `RequirementsHubSegula` possède deux espaces utilisateurs distincts et deux langages visuels s'inspirant de références d'excellence (Stripe pour le Portail Métier, Linear.app pour le Portail Ingénieur IA).

---

## 1. PORTAIL MÉTIER / SOUMETTEUR (`/portal`)
- **Inspiration Platforme :** Stripe Dashboard / Notion Workspaces (Warm Scandinavian Minimalist).
- **Philosophie :** Human-first, progressive disclosure, clarté absolue, absence de jargon technique.
- **Thème Visual Tokens :**
  - Background Canvas: `hsl(40, 30%, 97%)` (`#FBF9F5` stone light)
  - Card Surface: `hsl(0, 0%, 100%)` (`#FFFFFF` pure white)
  - Border Subtilité: `hsl(38, 15%, 88%)` (`#E5E2DC`)
  - Accent Primary: `hsl(24, 10%, 10%)` (`#1C1917` warm charcoal)
  - Accent Success / Active: `hsl(142, 45%, 38%)` (`#2D6A4F` deep sage)
- **Directives de composants (`/portal`) :**
  - **Formulaire Wizard Step-by-Step :** Un seul step affiché à la fois (`Progressive Disclosure`). Ne jamais afficher l'intégralité du formulaire d'un coup.
  - **Timeline de Statut Lisible :** Remplacer les valeurs d'enums brutes (`NEEDS_CLARIFICATION`, `GO`) par une timeline visuelle (`EN ATTENTE DE VALIDATION` → `ÉVALUATION IA` → `DOSSIER VALIDÉ`).
  - **Masquage strict des données internes :** Interdiction d'afficher `score`, `breakdown`, `reviewer_notes` ou `manual_override`.

---

## 2. DASHBOARD INGÉNIEUR IA & ADMIN (`/admin`)
- **Inspiration Platforme :** Linear.app / Vercel Dashboard (Obsidian High-Contrast Dark Mode).
- **Philosophie :** Densité d'information maximale, sobriété, keyboard-first, visibilité technique totale.
- **Thème Visual Tokens :**
  - Background Canvas: `hsl(240, 10%, 4%)` (`#09090B` obsidian dark)
  - Card / Row Surface: `hsl(240, 6%, 7%)` (`#121215`)
  - Border Line: `rgba(255, 255, 255, 0.1)` (`border-white/10`)
  - Primary Accent (Champagne Gold / Amber): `hsl(45, 65%, 52%)` (`#D4AF37`)
  - Status Badges:
    - `GO`: `hsl(142, 70%, 45%)` (Emerald Green)
    - `NO_GO`: `hsl(0, 72%, 51%)` (Crimson Red)
    - `NEEDS_CLARIFICATION`: `hsl(38, 92%, 50%)` (Amber Yellow)
- **Directives de composants (`/admin`) :**
  - **Tableau de soumissions dense :** Densité élevée (`py-2.5 px-4`), bordures horizontales fines (`border-b border-white/10`), actions inline.
  - **Score Breakdown Panel :** Affichage explicite du dict `breakdown` (7 critères de faisabilité IA avec jauges d'avancement).
  - **Override Drawer / Modal :** Formulaire direct d'override (`DecisionOverrideInput`) accessible sans quitter le tableau.

---

## 🚫 INTERDICTIONS ABSOLUES DE GENERATION (ANTI-AI SLOP)
1. **Pas de dégradé violet/bleu tech par défaut** (`from-indigo-600 to-purple-600`).
2. **Pas de cartes symétriques monotones** sans hiérarchie de typographie ni de bordures.
3. **Pas de boîtes d'alerte génériques** sans icônes contextuelles ou états d'interaction.
4. **Pas de transitions instantanées** — utiliser `transition-all duration-200 ease-out` sur tous les éléments interactifs.
