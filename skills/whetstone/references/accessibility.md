# Accessibility

Read this for any change to a user interface: web pages, single-page apps, mobile and desktop screens, emails and documents generated for users, and low-code apps. The target is WCAG 2.2 Level AA unless the project states a stricter one.

## Contents

- [Know the target](#know-the-target)
- [Use native semantics first](#use-native-semantics-first)
- [Make everything work with a keyboard](#make-everything-work-with-a-keyboard)
- [Name, label and announce](#name-label-and-announce)
- [Meet the visual thresholds](#meet-the-visual-thresholds)
- [Support every way of interacting](#support-every-way-of-interacting)
- [Test with tools and by hand](#test-with-tools-and-by-hand)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Know the target

WCAG 2.2 is the current W3C Recommendation (updated 12 December 2024) and is also published as ISO/IEC 40500:2025. Content that meets WCAG 2.2 also meets 2.1 and 2.0. In the European Union, the European Accessibility Act has applied since 28 June 2025 to many consumer products and services, including e-commerce, banking services and e-books, so accessibility is a legal requirement for many products, not only good practice.

Accessibility is part of the definition of done for UI work. Retrofitting it after release costs far more than building it in.

## Use native semantics first

The ARIA Authoring Practices Guide (APG) opens with the principle "No ARIA is better than Bad ARIA": ARIA roles change what assistive technology announces, but they add no keyboard behaviour or styling.

Apply it:

1. Use the native element for the job: `<button>` for actions, `<a href>` for navigation, `<label>` with form controls, `<table>` for tabular data, headings in order, landmarks (`<main>`, `<nav>`, `<header>`, `<footer>`).
2. Add ARIA only when no native element fits, and then implement the full keyboard behaviour that the role promises.
3. For custom widgets (tabs, comboboxes, menus, dialogs, tree views), follow the matching APG pattern exactly, including its keyboard interactions.
4. Never put `aria-hidden="true"` or `role="presentation"` on focusable elements or their ancestors.

Bad:

```html
<div class="btn" onclick="save()">Save</div>
```

Good:

```html
<button type="button" onclick="save()">Save</button>
```

## Make everything work with a keyboard

Apply it:

1. Make every function available from the keyboard, with a logical focus order and no keyboard traps.
2. Keep the focus indicator visible, and make sure sticky headers, banners and chat widgets do not entirely hide the focused element.
3. For a modal dialog, prefer the native `<dialog>` element opened with `showModal()`, which makes the rest of the page inert and closes on Escape. A custom dialog needs the full APG dialog pattern: `role="dialog"`, `aria-modal="true"` and a name through `aria-labelledby`, focus moved into the dialog when it opens, Tab and Shift+Tab kept inside it, Escape to close. Either way, check that focus returns to the control that opened it.
4. When content changes after an action (a route change, a deleted row), move focus somewhere sensible instead of leaving it on a removed element.

## Name, label and announce

Apply it:

1. Give every control an accessible name that matches or contains its visible label.
2. Give every informative image a text alternative that conveys its purpose; give decorative images an empty `alt=""`.
3. Label every form field, mark required fields in text and not by colour alone, and connect hints and errors to their fields programmatically.
4. On validation failure, identify the field in text, explain how to fix it, and keep the user's input.
5. Announce status updates that do not move focus (saved, three results found, upload complete) with a live region.
6. Set the page language, write unique page titles, and make link text meaningful out of context.

## Meet the visual thresholds

| Success criterion (level) | Requirement in brief |
|---|---|
| 1.4.1 Use of Color (A) | Colour is never the only way information is conveyed |
| 1.4.3 Contrast (Minimum) (AA) | Text contrast at least 4.5:1; large text (18 point, or 14 point bold) at least 3:1 |
| 1.4.4 Resize Text (AA) | Text can be resized to 200 percent without loss of content or function |
| 1.4.10 Reflow (AA) | Content works at a width of 320 CSS pixels (1280 pixels at 400 percent zoom) without two-dimensional scrolling |
| 1.4.11 Non-text Contrast (AA) | Component boundaries, states, focus indicators and meaningful graphics at least 3:1 against adjacent colours |
| 1.4.12 Text Spacing (AA) | Nothing breaks when users set line height to 1.5, paragraph spacing to 2, letter spacing to 0.12 and word spacing to 0.16 times the font size |
| 2.4.7 Focus Visible (AA) | Keyboard focus is always visible |
| 2.4.11 Focus Not Obscured (Minimum) (AA) | The focused element is not entirely hidden by author content |
| 2.5.8 Target Size (Minimum) (AA) | Pointer targets at least 24 by 24 CSS pixels, or spaced so that 24-pixel circles around them do not overlap, with listed exceptions such as inline links |

## Support every way of interacting

Apply it:

1. Provide a single-pointer alternative for any dragging interaction, such as buttons to reorder items (2.5.7 Dragging Movements, AA).
2. Never make authentication depend on memorising, transcribing or solving something without an alternative (3.3.8 Accessible Authentication (Minimum), AA). Allow paste and password managers, and let users paste one-time codes.
3. Do not ask for information the user already gave in the same process; prefill it or let them select it (3.3.7 Redundant Entry, A).
4. Keep help mechanisms in the same relative place across pages (3.2.6 Consistent Help, A).
5. Let users extend or turn off time limits, and respect the reduced-motion preference for non-essential animation.
6. Provide captions for video with speech, and transcripts for audio.

## Test with tools and by hand

The W3C states that evaluation tools cannot determine accessibility, only assist in doing so. The axe-core project claims its rules find on average 57 percent of WCAG issues automatically; the rest need a human.

Apply it:

1. Run an automated checker in the test suite, for example axe-core through `@axe-core/playwright`, filtered to the WCAG A and AA tags including `wcag22aa`. Treat new violations as test failures.
2. Write component tests that find elements by role and accessible name, so the tests fail when semantics break.
3. Do a keyboard-only pass of every changed flow: reach, operate and leave every control; check visible focus and order.
4. Zoom to 400 percent (or set a 320 CSS pixel viewport) and check that nothing is cut off or needs horizontal scrolling.
5. For T2 and above UI changes, do a short screen reader pass (for example NVDA on Windows or VoiceOver on macOS and iOS) of the main flow, listening for names, roles, states and announcements.
6. Report what you could not test. An agent without a screen reader must say so instead of claiming conformance.

Check:

- [ ] No new automated violations at WCAG 2.2 A and AA.
- [ ] Every changed flow works with the keyboard alone, with visible focus.
- [ ] Contrast, reflow and target size meet the thresholds above.
- [ ] Manual checks performed, and those not performed, are listed in the PR.

## Failure modes

- Clickable `div` elements that a mouse can use and a keyboard cannot reach.
- ARIA added to "fix" a widget, which now announces a role whose keyboard behaviour is missing.
- A modal that lets focus escape behind it, or that never returns focus on close.
- Placeholder text used as the only label, which disappears as soon as the user types.
- An automated scan passes, and the team declares the page accessible without a single manual check.
- A login form that blocks paste, which fails the accessible authentication criterion and annoys every password manager user.

## Sources

- W3C, [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/), and the [WCAG overview](https://www.w3.org/WAI/standards-guidelines/wcag/) give the criteria, levels and ISO status. WCAG is published under the W3C document licence, so this file paraphrases it.
- W3C Understanding documents: [Target Size (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html), [Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) and [Accessible Authentication (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html).
- W3C, [ARIA Authoring Practices Guide: Read Me First](https://www.w3.org/WAI/ARIA/apg/practices/read-me-first/) and [Dialog (Modal) pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/).
- MDN, [The dialog element](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog), documents that `showModal()` makes the rest of the page inert and that Escape closes a modal dialog.
- W3C, [Selecting Web Accessibility Evaluation Tools](https://www.w3.org/WAI/test-evaluate/tools/selecting/), explains the limits of automated tools.
- Deque, [axe-core](https://github.com/dequelabs/axe-core) and its [API tags](https://github.com/dequelabs/axe-core/blob/develop/doc/API.md); Playwright, [Accessibility testing](https://playwright.dev/docs/accessibility-testing).
- European Commission, [European Accessibility Act](https://commission.europa.eu/strategy-and-policy/policies/justice-and-fundamental-rights/disability/union-equality-strategy-rights-persons-disabilities-2021-2030/european-accessibility-act_en), lists covered products and services; AccessibleEU confirms [the 28 June 2025 application date](https://accessible-eu-centre.ec.europa.eu/content-corner/news/eaa-comes-effect-june-2025-are-you-ready-2025-01-31_en).
