# Traceability report: C:\Users\gmthj\nodrive\SE201\demo-shop

- **Repo:** C:\Users\gmthj\nodrive\SE201\demo-shop
- **Checked:** 2026-11-09 21:25 UTC with `gpt-6-luna`, prompt `agent_v1` (agent, at most 10 read-only tool calls per criterion)

## Summary: 3 of 7 covered, 3 not covered, 1 partial

| # | Acceptance criterion | Verdict | Tests cited |
|---|---|---|---|
| AC1 | Given an empty cart, when the shopper adds 2 of an item, then the cart holds 2 of that item. | **covered** | `test_add_item` |
| AC2 | Given a cart, when the shopper adds an item with a quantity of 0 or less, then a ValueError is raised and the cart is unchanged. | **not covered** | none |
| AC3 | Given a cart with a subtotal of $50 or more, when the shopper applies the code SAVE10, then the subtotal drops by 10%. | **covered** | `test_save10_takes_10_percent_off` |
| AC4 | Given an expired discount code, when the shopper applies it, then an "expired" error is raised and the subtotal is unchanged. | **partial** | `test_expired_code_is_rejected` |
| AC5 | Given a discount code that was already used on the cart, when the shopper applies it again, then it is rejected with an error. | **not covered** | `test_apply_code_twice` |
| AC6 | Given a cart with items, when the shopper checks out, then the receipt total is the subtotal plus 9% GST. | **covered** | `test_receipt_total_includes_gst` |
| AC7 | Given an empty cart, when the shopper checks out, then an error is raised and no receipt is created. | **not covered** | `test_checkout_empty_cart` |

## Details

### AC1: covered

> Given an empty cart, when the shopper adds 2 of an item, then the cart holds 2 of that item.

**Why:** The test starts with an empty cart, adds 2 apples, and asserts that the cart’s apple quantity is 2.

**Tests:** `tests/test_cart.py::test_add_item`

**Next step:** Nothing to do.

<sub>Agent steps (2): search_tests(Given an empty cart, when shopper adds quantity 2 of an item); read_file(tests/test_cart.py, 1)</sub>

### AC2: not covered

> Given a cart, when the shopper adds an item with a quantity of 0 or less, then a ValueError is raised and the cart is unchanged.

**Why:** The cart tests exercise adding items with positive quantities, but none adds an item with a quantity of 0 or less or checks that the cart remains unchanged after a ValueError.

**Next step:** Write a test for this criterion; related tests do not check it.

<sub>Agent steps (4): search_tests(Test shopper adding cart item with zero or negative quantity); grep(add_item|ValueError|quantity, tests); grep(def add_item|class Cart, ); read_file(tests/test_cart.py, 1)</sub>

### AC3: covered

> Given a cart with a subtotal of $50 or more, when the shopper applies the code SAVE10, then the subtotal drops by 10%.

**Why:** The test creates a cart with a $60 item, applies SAVE10, and asserts the result is $54—a 10% reduction.

**Tests:** `tests/test_discounts.py::test_save10_takes_10_percent_off` (line 18)

**Next step:** Nothing to do.

<sub>Agent steps (2): search_tests(Given a cart with subtotal of $50 or more, when shopper appl); read_file(tests/test_discounts.py, 1)</sub>

### AC4: partial

> Given an expired discount code, when the shopper applies it, then an "expired" error is raised and the subtotal is unchanged.

**Why:** The test applies an expired code and asserts that an error matching "expired" is raised, but it does not assert that the subtotal remains unchanged.

**Tests:** `tests/test_discounts.py::test_expired_code_is_rejected` (line 36)

**Next step:** Add the missing checks to the test (the reason says what is unchecked).

<sub>Agent steps (3): search_tests(expired discount code applied by shopper raises an expired e); grep(expired|discount|coupon|subtotal, ); read_file(tests/test_discounts.py, 1)</sub>

### AC5: not covered

> Given a discount code that was already used on the cart, when the shopper applies it again, then it is rejected with an error.

**Why:** `test_apply_code_twice` applies the same code twice to the same cart, but its `try/except` passes whether or not the second application raises an error. It does not assert rejection.

**Tests:** `tests/test_discounts.py::test_apply_code_twice` (line 42)

**Next step:** Write a test for this criterion; related tests do not check it.

<sub>Agent steps (1): search_tests(Tests for applying a discount or coupon code to a cart, espe)</sub>

### AC6: covered

> Given a cart with items, when the shopper checks out, then the receipt total is the subtotal plus 9% GST.

**Why:** The test adds an item to a cart and checks out; it asserts GST of 5.40 and a receipt total of 65.40, confirming the total includes 9% GST on the item subtotal.

**Tests:** `tests/test_checkout.py::test_receipt_total_includes_gst` (line 9)

**Next step:** Nothing to do.

<sub>Agent steps (1): search_tests(checkout cart items receipt total subtotal plus 9% GST tax c)</sub>

### AC7: not covered

> Given an empty cart, when the shopper checks out, then an error is raised and no receipt is created.

**Why:** The test named `test_checkout_empty_cart` adds bread before checkout, so it does not test checkout with an empty cart. No shown test asserts that checkout raises an error or creates no receipt for an empty cart.

**Tests:** `tests/test_checkout.py::test_checkout_empty_cart` (line 26)

**Next step:** Write a test for this criterion; related tests do not check it.

<sub>Agent steps (2): search_tests(empty cart shopper checks out; expect an error and verify no); grep(checkout|empty|raises|receipt, tests)</sub>

---
Generated by an AI agent: check a verdict before acting on it.
