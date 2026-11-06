# Small decisions that make the app useful

[Back to Brújula](../README.md) · [Product tour](PRODUCT_TOUR.md)

## Two identical coffees can both be real

An imported €2.50 purchase matches another purchase on date, account, description and amount, but has no stable external reference. Deleting it automatically could remove a real second purchase. The selected logic returns a possible match for review. A matching stable reference is stronger evidence; a matching reference with a different amount is a conflict. The runnable [demo](../bin/demo.dart) and [tests](../test/finance_review_test.dart) cover these distinctions.

## Spending is not the same as money leaving the account

The expanded gallery contains €650 housing, €190 groceries and €45 transport, with a €25 refund. Net classified spending is `650 + 190 + 45 − 25 = €860`. With €2,400 income, generated savings are `2,400 − 860 = €1,540`. A €300 transfer is separate. Another €12.50 is pending classification and remains visible outside the classified total. These are invented figures, not personal financial results.

## Unknown investment value is not a loss

The priced positions show `€2,200 − €2,000 = +€200` and `€980 − €1,000 = −€20`, giving `+€180`. A third position has €150 recorded cost but no confirmed value. Its unknown value is excluded from that gain calculation and flagged in the interface.

## A pending exam is not a zero

An assignment scores 8/10 and represents 40% of the course; the 60% exam is pending. The assessed average is 8/10, while completed assessment weight is 40%. That is neither a final grade nor a 3.2/10 failure. The academic view keeps progress and pending assessment distinct.

## Shopping needs depend on units

Two planned rice recipes need 160 g each. With 100 g in stock, the shortfall is `2 × 160 − 100 = 220 g`. The tomatoes in this fixture are recorded in pieces, while the recipe needs grams; no invented conversion is applied. A usable shopping list needs that uncertainty preserved.

## One day can have two energy records without adding them

The fictional diary records 450 and 650 kcal: 1,100 kcal in food entries. An older manual daily total of 2,100 kcal is retained as an alternative source. The selected source is displayed; 3,200 kcal would double-count the two records. The screen also keeps missing nutrient data explicit.

Only the import-review examples are included in this repository's executable extraction. The other examples explain the rendered original app views; their complete implementations remain private.
