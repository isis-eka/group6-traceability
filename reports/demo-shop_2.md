# Traceability report: C:\Users\gmthj\nodrive\SE201\demo-shop

- **Repo:** C:\Users\gmthj\nodrive\SE201\demo-shop
- **Checked:** 2026-11-09 21:27 UTC with `gpt-6-luna`, prompt `agent_v1` (agent, at most 10 read-only tool calls per criterion)

## Summary: 2 of 7 covered, 2 partial, 3 not covered

| # | Acceptance criterion | Verdict | Tests cited |
|---|---|---|---|
| AC1 | Given an empty cart, when the shopper adds 2 of an item, then the cart holds 2 of that item. | **partial** | `test_subtotal` |
| AC2 | Given a cart, when the shopper adds an item with a quantity of 0 or less, then a ValueError is raised and the cart is unchanged. | **not covered** | none |
| AC3 | Given a cart with a subtotal of $50 or more, when the shopper applies the code SAVE10, then the subtotal drops by 10%. | **covered** | `test_save10_takes_10_percent_off` |
| AC4 | Given an expired discount code, when the shopper applies it, then an "expired" error is raised and the subtotal is unchanged. | **partial** | `test_expired_code_is_rejected` |
| AC5 | Given a discount code that was already used on the cart, when the shopper applies it again, then it is rejected with an error. | **not covered** | `test_apply_code_twice` |
| AC6 | Given a cart with items, when the shopper checks out, then the receipt total is the subtotal plus 9% GST. | **covered** | `test_receipt_total_includes_gst` |
| AC7 | Given an empty cart, when the shopper checks out, then an error is raised and no receipt is created. | **not covered** | `test_checkout_empty_cart` |

## Details

### AC1: partial

> Given an empty cart, when the shopper adds 2 of an item, then the cart holds 2 of that item.

**Why:** `test_subtotal` starts with an empty cart and adds 2 apples, but also adds bread; it asserts the subtotal rather than the apple quantity, so it does not directly verify that the cart holds 2 apples.

**Tests:** `tests/test_cart.py::test_subtotal` (line 22)

**Next step:** Add the missing checks to the test (the reason says what is unchecked).

<sub>Agent steps (2): search_tests(Test that starting with an empty cart, adding quantity 2 of ); read_file(tests/test_cart.py, 1)</sub>

### AC2: not covered

> Given a cart, when the shopper adds an item with a quantity of 0 or less, then a ValueError is raised and the cart is unchanged.

**Why:** The tests exercise adding positive quantities, but none adds an item with a quantity of zero or less and checks for a ValueError or an unchanged cart.

**Next step:** Write a test for this criterion; related tests do not check it.

<sub>Agent steps (4): search_tests(Cart adding item quantity zero or negative raises ValueError); read_file(tests/test_cart.py, 1); grep(add_item|ValueError|quantity, tests); grep(def add_item|class Cart, .)</sub>

### AC3: covered

> Given a cart with a subtotal of $50 or more, when the shopper applies the code SAVE10, then the subtotal drops by 10%.

**Why:** The test creates a cart with a $60 subtotal, applies SAVE10, and asserts the result is $54, a 10% reduction.

**Tests:** `tests/test_discounts.py::test_save10_takes_10_percent_off` (line 18)

**Next step:** Nothing to do.

<sub>Agent steps (2): search_tests(A cart has subtotal of at least $50; shopper applies coupon/); read_file(tests/test_discounts.py, 1)</sub>

### AC4: partial

> Given an expired discount code, when the shopper applies it, then an "expired" error is raised and the subtotal is unchanged.

**Why:** The test applies an expired code and asserts that an error containing “expired” is raised, but it does not assert that the subtotal remains unchanged.

**Tests:** `tests/test_discounts.py::test_expired_code_is_rejected` (line 36)

**Next step:** Add the missing checks to the test (the reason says what is unchecked).

<sub>Agent steps (2): search_tests(Test applying an expired discount code: it raises an expired); read_file(tests/test_discounts.py, 1)</sub>

### AC5: not covered

> Given a discount code that was already used on the cart, when the shopper applies it again, then it is rejected with an error.

**Why:** test_apply_code_twice applies the same code twice, but it only catches DiscountError; it passes even if the second application raises no error, so rejection is not verified.

**Tests:** `tests/test_discounts.py::test_apply_code_twice` (line 42)

**Next step:** Write a test for this criterion; related tests do not check it.

<sub>Agent steps (2): search_tests(test applying a discount code or coupon to a cart when the s); read_file(tests/test_discounts.py, 1)</sub>

### AC6: covered

> Given a cart with items, when the shopper checks out, then the receipt total is the subtotal plus 9% GST.

**Why:** The test adds a $60 item, checks out the cart, and asserts GST of $5.40 and a receipt total of $65.40, matching subtotal plus 9% GST.

**Tests:** `tests/test_checkout.py::test_receipt_total_includes_gst` (line 9)

**Next step:** Nothing to do.

<sub>Agent steps (2): search_tests(Given a cart with items, when the shopper checks out, then t); read_file(tests/test_checkout.py, 1)</sub>

### AC7: not covered

> Given an empty cart, when the shopper checks out, then an error is raised and no receipt is created.

**Why:** The closest test adds bread before checkout, so the cart is not empty. It asserts receipt text, not that checkout raises an error or creates no receipt.

**Tests:** `tests/test_checkout.py::test_checkout_empty_cart` (line 26)

**Next step:** Write a test for this criterion; related tests do not check it.

<sub>Agent steps (4): search_tests(Given an empty cart, when the shopper checks out, then an er); read_file(tests/test_checkout.py, 1); grep(checkout\(, tests); grep(empty|receipt|raises|Error, tests)</sub>

---
Generated by an AI agent: check a verdict before acting on it.
