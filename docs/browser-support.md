# Browser support and accessibility

## Support target

- Latest stable Chrome and Microsoft Edge: primary desktop target.
- Latest stable Firefox: supported through standards-based APIs; scheduled for CI expansion after the demo release.
- Safari: functional target, but Canvas download and drag/drop require release-device verification.
- Minimum desktop layout width: 1080 px. Mobile optimization is outside `v0.7.0-demo` scope.

## Accessibility baseline

- Semantic headings, navigation, tables, forms, status/alert regions, and dialog labels.
- Keyboard skip link and visible focus indicators.
- Tier movement has select/button alternatives to drag-and-drop.
- Color is paired with text labels and source symbols.
- Detail dialog closes by button, backdrop, or Escape.
- Charts expose accessible names; source values and freshness are also available as text.

Automated Chromium E2E covers critical interactions. A formal WCAG audit and screen-reader matrix remain pre-1.0 work.
