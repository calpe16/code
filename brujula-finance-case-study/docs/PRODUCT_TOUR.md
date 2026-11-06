# A tour of Brújula

[Back to the project](../README.md) · [Technical notes](TECHNICAL.md)

**Synthetic demo data.** These are local renders of the app’s Flutter widgets with a new in-memory fixture. The interface is in Spanish; the captions explain what to look for. Most module captures isolate the original page widget inside a labelled capture frame; the home capture uses the full app shell.

## Start with today

The real application shell brings daily habits, plans and a financial summary together. The demo banner is part of the app; no Google account is connected.

![Start with today — real Brújula screen with fictional data](../media/home-desktop.png)

## Understand the month

The financial overview separates classified spending from a pending transaction. A transfer is not treated as consumption. All balances are fictional and are not reconciled bank statements.

![Understand the month — real Brújula screen with fictional data](../media/finance-desktop.png)

## Read investment values carefully

The two priced holdings have a combined €180 gain. The third has no confirmed value and is excluded from that calculation, rather than silently treated as a total loss.

![Read investment values carefully — real Brújula screen with fictional data](../media/investments-desktop.png)

## Give savings a purpose

Virtual savings allocations use the cash actually recorded. The view warns when manual reserves exceed available cash; it does not move money or anticipate future salaries.

![Give savings a purpose — real Brújula screen with fictional data](../media/goals-desktop.png)

## Make progress visible

Daily habits, tasks and consistency over time. The fictional reading habit has several check-ins; the other habits are still open.

![Make progress visible — real Brújula screen with fictional data](../media/habits-desktop.png)

## Find documents and their context

A searchable library of invented document metadata and text. These demonstration records have no underlying PDF attached. Opening a real original, OCR and cloud indexing are outside this capture.

![Find documents and their context — real Brújula screen with fictional data](../media/documents-desktop.png)

## Keep pending grades pending

A fictional course includes an assessed assignment and an assessment still to come. Partial progress uses assessed weight; an ungraded item is not entered as zero. The Drive index is disconnected.

![Keep pending grades pending — real Brújula screen with fictional data](../media/study-desktop.png)

## Review personal wellbeing

Fictional sleep, weight and energy records, with trends and explicit record coverage. These are personal tracking views, not clinical assessments.

![Review personal wellbeing — real Brújula screen with fictional data](../media/wellbeing-desktop.png)

## Plan meals and shopping together

Two fictional recipes feed the plan and shopping calculation. Stock is subtracted only when units can be reconciled; menu cost is an estimate, not a retailer quote.

![Plan meals and shopping together — real Brújula screen with fictional data](../media/meals-desktop.png)

## Account for what is already there

The fictional pantry contains rice measured in grams and tomatoes measured in pieces. The app keeps those units explicit.

![Account for what is already there — real Brújula screen with fictional data](../media/pantry-desktop.png)

## Separate a plan from completion

A planned mobility session remains marked as uncompleted.

![Separate a plan from completion — real Brújula screen with fictional data](../media/training-desktop.png)

## Keep food records understandable

Two fictional food entries total 1,100 kcal. A separate manual total remains available; the two sources are never added together. Missing nutrition fields remain missing.

![Keep food records understandable — real Brújula screen with fictional data](../media/food-diary-desktop.png)

## The same workspace on a smaller screen

The real financial, habit and food-diary widgets were also rendered at a 430-pixel phone width. These are viewport renders, not photographs or tests on a physical phone.

<p><img src="../media/finance-mobile.png" alt="Financial overview at phone width" width="30%"> <img src="../media/habits-mobile.png" alt="Habits at phone width" width="30%"> <img src="../media/food-diary-mobile.png" alt="Food diary at phone width" width="30%"></p>
