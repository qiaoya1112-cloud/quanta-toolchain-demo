# AI Workflow Visual V2 Design

## Objective

Create a visually richer version of the existing AI workflow sharing page while preserving its current content, information architecture, and interactions.

The new version must make the page feel less empty and improve section hierarchy without changing the workflow narrative.

## Version Strategy

- Preserve `ai-workflow-share-enhanced.html` without modification.
- Create `ai-workflow-share-enhanced-v2.html` as the new visual version.
- Keep both files independently accessible for side-by-side comparison.
- Do not introduce a framework, build tool, or external component dependency.

## Scope

### Included

- Page canvas and section background colors
- Background depth and restrained atmospheric decoration
- Card surfaces, borders, shadows, and hover states
- Typography contrast and visual hierarchy
- Modal surface styling
- Consistent spacing and section separation
- Lightweight entrance and hover motion
- Responsive visual behavior

### Excluded

- Content rewrites
- Human decision-point content
- Architecture diagrams
- Data-flow content
- Workflow stage changes
- New sections or routes
- Changes to modal content or JavaScript behavior
- React, Vue, Ant Design, or other framework migration

## Design Read

This is an internal product-method sharing microsite for product managers and cross-functional colleagues. The visual language should feel professional, calm, and technical rather than promotional or highly experimental.

Design controls:

- Design variance: 6/10
- Motion intensity: 3/10
- Visual density: 5/10
- Theme: light, cool technical paper
- Accent: one consistent cobalt-blue family

## Visual Direction

### Page Canvas

Use a cool gray-blue canvas instead of pure white.

Suggested semantic tokens:

- Page canvas: `#F3F6FA`
- Primary section surface: `#F8FAFC`
- Emphasized section surface: `#EAF1F8`
- Card surface: `rgba(255, 255, 255, 0.94)`
- Primary text: `#102033`
- Secondary text: `#52657A`
- Border: `#D9E3EE`
- Accent: `#2563EB`

Final values may be calibrated during browser verification, but the palette must remain within one cool neutral family.

### Background Treatment

- Replace the nearly invisible global animated background with section-aware background depth.
- Use at most two or three large, low-saturation radial color fields across the full page.
- Keep decorative color opacity between approximately 4% and 8%.
- Avoid purple AI gradients, noisy mesh effects, decorative grids, and strong neon glow.
- Background decoration must never reduce text contrast or compete with content.

### Section Hierarchy

- Maintain one light theme throughout the page.
- Alternate sections through subtle surface changes rather than pure white blocks.
- Use spacing and background tone before adding more card containers.
- Preserve the existing section order and anchor behavior.

### Cards

- Keep the existing soft-radius language.
- Use tinted shadows that match the cool page canvas.
- Reduce heavy hover translation and use restrained lift or border emphasis.
- Preserve all card content and click behavior.

### Header

- Preserve the current title, subtitle, metrics, and layout.
- Replace the plain white background with a restrained cool atmospheric field.
- Keep the hero readable within the initial desktop viewport.
- Avoid adding new labels, CTAs, or decorative text.

### Workflow and Modals

- Preserve all three workflow stages and their current interaction logic.
- Improve stage separation through surface contrast and connector clarity.
- Restyle modal backgrounds, borders, sidebar surfaces, and shadows within the same palette.
- Do not change modal dimensions, step content, or tool tags unless required for contrast.

## Motion

- Keep existing reveal behavior where it works.
- Animate only opacity and transform.
- Reduce decorative background motion and prioritize stable reading.
- Respect `prefers-reduced-motion` by disabling nonessential animation.
- Do not add scroll hijacking, parallax, or continuous cursor effects.

## Responsive Behavior

- Preserve the existing responsive structure.
- Ensure the new background treatment does not create horizontal overflow.
- Decorative fields must remain clipped inside their sections.
- Cards and modal surfaces must retain sufficient contrast on narrow screens.

## Accessibility

- Body text must meet WCAG AA contrast against every section surface.
- Interactive states must remain visible without relying only on color.
- Focus styles must stay visible.
- Reduced-motion users must receive a stable page.

## Acceptance Criteria

1. The original HTML file is unchanged.
2. The V2 file opens independently and preserves all existing content and interactions.
3. The page no longer reads as a mostly empty white canvas.
4. Section hierarchy remains clear without introducing a dark theme.
5. One coherent cool gray-blue palette is used across the full page.
6. Workflow cards and all three modals remain functional.
7. The page has no new horizontal overflow at desktop or mobile widths.
8. Reduced-motion behavior is supported.
9. Browser screenshots confirm readable contrast and consistent surfaces.

## Verification Plan

- Compare the original and V2 pages side by side.
- Capture the V2 overview and the first two modal states.
- Verify desktop and narrow viewport behavior.
- Check console errors.
- Confirm the original file has no diff.
- Confirm all three workflow stage controls still open the correct modal.
